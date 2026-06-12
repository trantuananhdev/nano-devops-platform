# Security Design

> **Audience:** CTO, Security Reviewer
> **Mục đích:** Giải thích các security decisions — từ API keys đến sandbox execution.

---

## Security Layers

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: Network Security                              │
│  • Traefik TLS termination (HTTPS only)                 │
│  • Docker internal network (services không expose port) │
│  • LLM node accessible chỉ qua internal IP             │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  LAYER 2: Authentication & Authorization                │
│  • API Keys: hashed (bcrypt), prefixed, expirable       │
│  • MCP Server: X-MCP-API-Key header required            │
│  • DB-first key lookup, .env fallback                   │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  LAYER 3: Container Security                            │
│  • Non-root containers (no --privileged)                │
│  • Read-only filesystem where possible                  │
│  • Resource limits on all services                      │
│  • No secrets in environment variables (Docker secrets) │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  LAYER 4: Agent Execution Security                      │
│  • Docker Sandbox: --network none --read-only           │
│  • Input validation on all tool calls                   │
│  • eval() whitelist (không cho arbitrary code)          │
│  • Audit log mọi tool execution                         │
└─────────────────────────────────────────────────────────┘
```

---

## API Key Management

**Thiết kế:** Không bao giờ store plaintext API key.

```python
# api_key_service.py
class ApiKey(Base):
    id: int
    name: str
    key_type: str          # gemini | mcp | minio | internal
    key_prefix: str        # Hiện thị: "hdtv_abc..."
    hashed_key: str        # bcrypt hash — không thể reverse
    is_active: bool
    created_by: str
    last_used_at: datetime

def create_key(name: str, key_type: str) -> tuple[str, ApiKey]:
    raw_key = f"hdtv_{secrets.token_urlsafe(32)}"  # Random key
    hashed = bcrypt.hashpw(raw_key.encode(), bcrypt.gensalt())
    db_key = ApiKey(
        key_prefix=raw_key[:12],    # Chỉ lưu prefix để identify
        hashed_key=hashed.decode()
    )
    return raw_key, db_key  # raw_key hiện 1 lần duy nhất, không lưu

def verify_key(raw_key: str) -> ApiKey | None:
    # DB-first lookup bằng prefix
    candidate = db.query(ApiKey).filter(
        ApiKey.key_prefix == raw_key[:12],
        ApiKey.is_active == True
    ).first()
    if candidate and bcrypt.checkpw(raw_key.encode(), candidate.hashed_key.encode()):
        return candidate
```

**Fallback chain:**
```
1. DB lookup (active key, hashed verify)
2. .env MCP_API_KEY (legacy fallback)
3. Dev mode: no key required (if not configured)
```

---

## Docker Sandbox — Agent Code Execution

Agent có thể cần chạy script tính toán (VD: kiểm tra compliance formula). Sandbox đảm bảo code không escape container:

```python
# docker_sandbox.py
class DockerSandboxExecutor:
    async def run_python_snippet(self, code: str, task_id: str) -> SandboxResult:
        cmd = [
            "docker", "run",
            "--rm",                      # Xóa container sau khi xong
            "--network", "none",         # Không có network access
            "--memory", "64m",           # Giới hạn RAM
            "--cpus", "0.5",             # Giới hạn CPU
            "--read-only",               # Filesystem read-only
            "--security-opt", "no-new-privileges",
            "python:3.11-alpine",
            "python", "-c", code
        ]
        proc = await asyncio.create_subprocess_exec(*cmd, ...)
        # Hard timeout: 15s
        await asyncio.wait_for(proc.wait(), timeout=15)
```

**Fallback:** Nếu Docker socket không available → process-level sandbox (giới hạn builtins).

**Audit:** Mọi sandbox execution → `AiAuditLog` với `tool_name="SandboxShell"`.

---

## eval() Hardening

```python
# react_agent.py — safe rule evaluation
SAFE_BUILTINS = {
    "len": len, "any": any, "all": all,
    "sum": sum, "min": min, "max": max,
    "bool": bool, "int": int, "str": str,
    "list": list, "dict": dict,
}

def _eval_rule_expression(expr: str, context: dict) -> bool:
    # Context có sẵn: failed, passed, failed_tools
    safe_context = {**SAFE_BUILTINS, **context}
    return eval(expr, {"__builtins__": {}}, safe_context)
    # __builtins__: {} ngăn import, exec, __class__, etc.
```

**Tại sao không dùng ast.literal_eval?** Vì cần evaluate boolean expressions (any, all, len). `literal_eval` chỉ cho literals.

---

## Secrets Management

```
Development:  .env file (gitignored)
Production:   Docker Secrets (files in /run/secrets/)

Không bao giờ:
- Hardcode secret trong code
- Commit .env vào Git
- Log secret values
- Expose secrets qua API response
```

```yaml
# docker-compose.hdtv.yml — Docker Secrets
secrets:
  hdtv_postgres_password:
    file: ./secrets/hdtv_postgres_password.txt

services:
  hdtv-postgres:
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/hdtv_postgres_password
    secrets:
      - hdtv_postgres_password
```

---

## Input Validation — Defense in Depth

```python
# tools/base.py — 3 levels of validation
async def execute_tool(name: str, params: dict):
    # Level 1: Schema validation (required fields + types)
    _validate_tool_input(name, params)

    # Level 2: Handler domain validation
    handler = get_handler(name)
    if handler:
        handler.validate_input(params)  # Domain-specific (VND ranges, doc_no format)

    # Level 3: Timeout guard
    result = await asyncio.wait_for(
        _run_tool(name, params),
        timeout=settings.tool_execution_timeout_s
    )
```

**Error taxonomy** (không leak implementation details):
```python
class ToolErrorType(str, Enum):
    TRANSIENT = "transient"     # Network/timeout — retry
    BAD_INPUT = "bad_input"     # Schema invalid — fix input
    UNAVAILABLE = "unavailable" # Tool down — fallback
    UNKNOWN = "unknown"         # Unexpected — retry 1x then escalate
```
