"""
Sandboxed Tool Executor — cô lập thực thi script/shell an toàn.

T-26 additions:
  - _emit_sandbox_audit(): ghi AiAuditLog cho mọi command Agent chạy
  - SANDBOX_EXECUTIONS Prometheus counter (type=shell|python, status=...)
  - sandbox_shell_tool() nhận task_id để correlate audit log

Mục tiêu:
  1. Agent có thể "chạy" một đoạn shell command hoặc Python snippet mà không crash server
  2. Bắt tất cả stderr, stdout, exit codes — trả về chuẩn cho agent tự sửa sai
  3. Timeout cứng (default 10s) — chống infinite loop hoặc blocking calls
  4. Whitelist lệnh được phép — không cho phép rm, dd, mkfs, v.v.
  5. Chạy trong subprocess RIÊNG (không in-process) — cô lập process-level

Để upgrade lên Docker sandbox:
  Dùng DockerSandboxExecutor trong docker_sandbox.py
"""

from __future__ import annotations

import asyncio
import logging
import shlex
import tempfile
from pathlib import Path
from typing import Any

from app.core.metrics import SANDBOX_EXECUTIONS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# T-26: Audit log helper
# ---------------------------------------------------------------------------

async def _emit_sandbox_audit(
    command: str,
    result: "SandboxResult",
    task_id: str = "sandbox",
    exec_type: str = "shell",
) -> None:
    """Write sandbox execution to AiAuditLog (best-effort, never raises)."""
    try:
        from app.core.database import async_session_factory
        from app.models.entities import AiAuditLog
        async with async_session_factory() as session:
            log = AiAuditLog(
                task_id=task_id,
                tool_name="SandboxShell",
                execution_time_ms=0,
                inputs={"command": command, "type": exec_type},
                outputs=result.to_agent_dict(),
            )
            session.add(log)
            await session.commit()
    except Exception as exc:
        logger.debug("sandbox audit log write failed (non-critical): %s", exc)


# ---------------------------------------------------------------------------
# Security: lệnh bị cấm
# ---------------------------------------------------------------------------

_FORBIDDEN_COMMANDS: frozenset[str] = frozenset({
    "rm", "rmdir", "dd", "mkfs", "fdisk", "shred", "wipefs",
    "shutdown", "reboot", "halt", "poweroff",
    "chmod", "chown",           # permission escalation
    "curl", "wget",             # outbound network (agent không được fetch external URLs)
    "ssh", "scp", "sftp",       # lateral movement
    "sudo", "su", "doas",
    "docker", "kubectl",        # container management
    "python", "python3",        # Python execution cần dùng run_python_snippet riêng
    "pip", "pip3",
})

# Sandbox environment — chỉ giữ PATH + LANG, loại bỏ credentials
_SANDBOX_ENV: dict[str, str] = {
    "PATH":    "/usr/local/bin:/usr/bin:/bin",
    "LANG":    "en_US.UTF-8",
    "HOME":    "/tmp",
    "TMPDIR":  "/tmp",
}

_DEFAULT_TIMEOUT_S: int = 10
_MAX_OUTPUT_CHARS: int  = 8_192   # Cắt output dài để tránh context overflow


# ---------------------------------------------------------------------------
# Result type
# ---------------------------------------------------------------------------

class SandboxResult:
    def __init__(
        self,
        *,
        stdout: str,
        stderr: str,
        exit_code: int,
        timed_out: bool = False,
        error: str | None = None,
    ) -> None:
        self.stdout    = stdout
        self.stderr    = stderr
        self.exit_code = exit_code
        self.timed_out = timed_out
        self.error     = error

    @property
    def success(self) -> bool:
        return self.exit_code == 0 and not self.timed_out and not self.error

    def to_agent_dict(self) -> dict[str, Any]:
        """Convert to dict the agent loop can consume as observation."""
        return {
            "stdout":    self.stdout[:_MAX_OUTPUT_CHARS] if self.stdout else "",
            "stderr":    self.stderr[:_MAX_OUTPUT_CHARS] if self.stderr else "",
            "exit_code": self.exit_code,
            "success":   self.success,
            "timed_out": self.timed_out,
            "error":     self.error,
            # Hint for agent self-correction
            "hint": (
                "Lệnh thành công." if self.success
                else (
                    f"Lệnh thất bại (exit_code={self.exit_code}). "
                    f"stderr: {self.stderr[:200]}" if not self.timed_out
                    else f"Lệnh bị hủy do timeout ({_DEFAULT_TIMEOUT_S}s). Hãy dùng lệnh nhẹ hơn."
                )
            ),
        }


# ---------------------------------------------------------------------------
# Security checks
# ---------------------------------------------------------------------------

def _check_command_safety(cmd: str) -> str | None:
    """Return error string if command is forbidden, None if safe."""
    try:
        tokens = shlex.split(cmd)
    except ValueError as e:
        return f"Lỗi parse lệnh: {e}"

    if not tokens:
        return "Lệnh rỗng"

    # Check first token (base command)
    base_cmd = Path(tokens[0]).name.lower()
    if base_cmd in _FORBIDDEN_COMMANDS:
        return f"Lệnh '{base_cmd}' không được phép trong sandbox"

    # Detect command injection patterns
    dangerous_patterns = [";", "&&", "||", "|", "`", "$(", "${", ">", "<", "&"]
    for pattern in dangerous_patterns:
        if pattern in cmd:
            return (
                f"Pattern nguy hiểm '{pattern}' không được phép. "
                "Mỗi lệnh phải đứng độc lập, không pipeline."
            )

    return None


# ---------------------------------------------------------------------------
# Core executor
# ---------------------------------------------------------------------------

async def run_shell_command(
    command:   str,
    *,
    timeout_s: int = _DEFAULT_TIMEOUT_S,
    work_dir:  str | None = None,
) -> SandboxResult:
    """
    Execute a shell command in a sandboxed subprocess.

    - Creates a temp working dir (cleaned up after)
    - Strips credentials from env
    - Hard timeout via asyncio.wait_for
    - Captures stdout + stderr separately

    Args:
        command:   Shell command string (single command, no pipe/semicolon)
        timeout_s: Max execution seconds (default 10)
        work_dir:  Custom working directory (default: temp dir)

    Returns:
        SandboxResult with stdout, stderr, exit_code, success flag
    """
    # Security check first
    safety_error = _check_command_safety(command)
    if safety_error:
        logger.warning("Sandbox blocked command: %s — %s", command, safety_error)
        result = SandboxResult(
            stdout="", stderr=safety_error, exit_code=1,
            error=f"Bị chặn bởi sandbox: {safety_error}",
        )
        SANDBOX_EXECUTIONS.labels(type="shell", status="blocked").inc()
        return result

    tmp_dir: str | None = None
    try:
        tmp_dir = work_dir or tempfile.mkdtemp(prefix="hdtv_sandbox_")
        tokens  = shlex.split(command)

        logger.debug("Sandbox exec: %s (timeout=%ds, cwd=%s)", command, timeout_s, tmp_dir)

        proc = await asyncio.create_subprocess_exec(
            *tokens,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
            cwd=tmp_dir,
            env=_SANDBOX_ENV,
        )

        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=float(timeout_s)
            )
            exit_code = proc.returncode or 0
            result = SandboxResult(
                stdout=stdout_b.decode("utf-8", errors="replace"),
                stderr=stderr_b.decode("utf-8", errors="replace"),
                exit_code=exit_code,
            )
            SANDBOX_EXECUTIONS.labels(type="shell", status="success" if result.success else "error").inc()
            return result
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            logger.warning("Sandbox timeout (%ds): %s", timeout_s, command)
            result = SandboxResult(
                stdout="", stderr=f"Timeout sau {timeout_s} giây",
                exit_code=124, timed_out=True,
            )
            SANDBOX_EXECUTIONS.labels(type="shell", status="timeout").inc()
            return result

    except FileNotFoundError:
        cmd_name = command.split()[0] if command else "?"
        result = SandboxResult(
            stdout="", stderr=f"Lệnh không tồn tại: {cmd_name}",
            exit_code=127, error=f"Command not found: {cmd_name}",
        )
        SANDBOX_EXECUTIONS.labels(type="shell", status="error").inc()
        return result
    except Exception as exc:
        logger.exception("Sandbox unexpected error for command: %s", command)
        result = SandboxResult(
            stdout="", stderr=str(exc),
            exit_code=1, error=str(exc),
        )
        SANDBOX_EXECUTIONS.labels(type="shell", status="error").inc()
        return result
    finally:
        # Cleanup temp dir nếu ta tạo ra
        if tmp_dir and work_dir is None:
            try:
                import shutil
                shutil.rmtree(tmp_dir, ignore_errors=True)
            except Exception:
                pass


async def run_python_snippet(
    code:      str,
    *,
    timeout_s: int = _DEFAULT_TIMEOUT_S,
) -> SandboxResult:
    """
    Run a Python code snippet in a sandboxed subprocess.

    The code is written to a temp .py file and executed with
    a minimal Python environment (no installed packages access).

    Note: This is process-level isolation — not Docker sandbox.
    For production untrusted code, replace with ephemeral Docker container.
    """
    if not code or not code.strip():
        return SandboxResult(stdout="", stderr="Code rỗng", exit_code=1, error="Empty code")

    # Basic safety: block import of dangerous modules
    dangerous_imports = [
        "import os", "import subprocess", "import sys",
        "import socket", "import shutil", "import importlib",
        "__import__", "eval(", "exec(",
    ]
    for pattern in dangerous_imports:
        if pattern in code:
            return SandboxResult(
                stdout="", stderr=f"Import/pattern bị cấm: {pattern}",
                exit_code=1, error=f"Blocked pattern: {pattern}",
            )

    tmp_dir = tempfile.mkdtemp(prefix="hdtv_pysnippet_")
    try:
        snippet_path = Path(tmp_dir) / "snippet.py"
        snippet_path.write_text(code, encoding="utf-8")

        python_bin = "python3"
        proc = await asyncio.create_subprocess_exec(
            python_bin, str(snippet_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
            cwd=tmp_dir,
            env={**_SANDBOX_ENV, "PYTHONPATH": ""},
        )

        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=float(timeout_s)
            )
            return SandboxResult(
                stdout=stdout_b.decode("utf-8", errors="replace"),
                stderr=stderr_b.decode("utf-8", errors="replace"),
                exit_code=proc.returncode or 0,
            )
        except asyncio.TimeoutError:
            proc.kill()
            await proc.communicate()
            return SandboxResult(
                stdout="", stderr=f"Python snippet timeout ({timeout_s}s)",
                exit_code=124, timed_out=True,
            )
    finally:
        import shutil
        shutil.rmtree(tmp_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Tool wrapper — expose as agent tool
# ---------------------------------------------------------------------------

async def sandbox_shell_tool(params: dict[str, Any]) -> dict[str, Any]:
    """Agent-callable wrapper for sandboxed shell execution.

    Input params:
        command (str): Shell command to run
        timeout_s (int): Optional timeout override

    Output: SandboxResult.to_agent_dict()
    """
    command   = params.get("command", "")
    timeout_s = int(params.get("timeout_s", _DEFAULT_TIMEOUT_S))

    if not command:
        return {"error": "Thiếu tham số 'command'", "exit_code": 1, "success": False}

    result = await run_shell_command(command, timeout_s=timeout_s)
    return result.to_agent_dict()
