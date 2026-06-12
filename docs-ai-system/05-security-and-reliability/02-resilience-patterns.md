# Resilience Patterns

> **Audience:** CTO, SRE
> **Mục đích:** Tất cả patterns để hệ thống không bao giờ hard-crash — circuit breaker, retry, degraded mode.

---

## Resilience Philosophy

**Nguyên tắc:** Hệ thống phải degrade gracefully, không hard-crash.

```
Hard crash (BAD):    Service → Error → 500 → User sees error page
Graceful degrade:   Service → Unavailable → Fallback → User sees partial result
                                                         với warning flag
```

Áp dụng cho mọi external dependency: LLM, Chroma, Meilisearch, MinIO.

---

## Pattern 1: Circuit Breaker (LLM)

Đã mô tả chi tiết trong `02-ai-agent-design/02-llm-router.md`.

**Tóm tắt:** CLOSED → OPEN (5 fails/60s) → HALF_OPEN (cooldown 30s) → CLOSED/OPEN.

---

## Pattern 2: Retry với Error Taxonomy

```python
# batch_executor.py
async def _run_one_with_retry(tool_name, params, max_retries=1, backoff=2.0):
    for attempt in range(max_retries + 1):
        result = await execute_tool(tool_name, params)
        error_type = result.get("error_type")

        if not error_type:
            return result  # Success

        if error_type == ToolErrorType.TRANSIENT:
            if attempt < max_retries:
                await asyncio.sleep(backoff)
                TOOL_RETRIES.labels(tool_name, error_type).inc()
                continue  # Retry
            # Max retries exhausted
        elif error_type == ToolErrorType.BAD_INPUT:
            break  # Don't retry — fix input first
        elif error_type == ToolErrorType.UNAVAILABLE:
            break  # Don't retry — use fallback

        return result  # Return error result

    return result
```

**Retry policy per error type:**

| Error Type | Retry? | Max attempts | Backoff |
|-----------|--------|-------------|---------|
| TRANSIENT | ✅ Yes | 2 | 2s |
| BAD_INPUT | ❌ No | 1 | — |
| UNAVAILABLE | ❌ No | 1 | — |
| UNKNOWN | ✅ Yes | 2 | 2s |

---

## Pattern 3: Degraded Mode

Mỗi external service có degraded fallback:

### Chroma → PostgreSQL fallback
```python
async def retrieve_relevant_memories(dossier_id, query, top_k):
    try:
        return await _query_chroma(query, top_k)
    except Exception:
        logger.warning("Chroma unavailable, degraded to PG scan")
        # Full table scan, trim
        rows = await db.execute(
            "SELECT observation FROM agent_memory WHERE dossier_id=$1 LIMIT $2",
            dossier_id, top_k
        )
        return [r.observation for r in rows]
```

### Meilisearch → Return empty with flag
```python
async def search_dossiers(query: str) -> SearchResult:
    try:
        return await meili_client.search(query)
    except Exception:
        logger.warning("Meilisearch unavailable, returning degraded result")
        return SearchResult(hits=[], _degraded=True)
        # Frontend shows "Tìm kiếm tạm thời không khả dụng" thay vì error
```

### MinIO → Return 404 gracefully
```python
async def get_pdf_url(dossier_id: int) -> str | None:
    dossier = await db.get(Dossier, dossier_id)
    if not dossier.pdf_url:
        raise HTTPException(404, "No PDF uploaded")  # Not 500
    try:
        return await minio_client.presigned_url(dossier.pdf_url)
    except MinioError:
        raise HTTPException(503, "File storage temporarily unavailable")
```

### LLM → Rule-based fallback
```python
# critic.py — fallback nếu LLM fail
async def review_draft(report_md, checks, risk_level):
    try:
        return await _call_llm_critic(report_md, checks, risk_level)
    except LLMUnavailableError:
        # Rule-based fallback
        failed_count = sum(1 for c in checks if not c.passed)
        return CriticVerdict(
            approved=(failed_count == 0 and risk_level != "HIGH"),
            issues=[f"{failed_count} checks failed"] if failed_count else [],
            suggested_fixes=[]
        )
```

---

## Pattern 4: Health Checks với depends_on

```yaml
# docker-compose.hdtv.yml
services:
  hdtv-api:
    depends_on:
      hdtv-postgres:
        condition: service_healthy  # Chờ PG healthy mới start API
      hdtv-chroma:
        condition: service_healthy
      hdtv-redis:
        condition: service_healthy

  hdtv-postgres:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hdtv"]
      interval: 10s
      timeout: 5s
      retries: 5

  hdtv-chroma:
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/heartbeat"]
      interval: 10s
```

**Rationale:** Không start service khi dependency chưa sẵn sàng → tránh startup errors.

---

## Pattern 5: LLM Client Retry

```python
# llm_client.py
async def call_llm(messages, **kwargs) -> str:
    for attempt in range(settings.llm_max_retries + 1):  # default: 2
        try:
            response = await httpx_client.post(url, json=payload, timeout=60)
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        except (httpx.TransportError, httpx.TimeoutException) as e:
            if attempt < settings.llm_max_retries:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                continue
            # All retries exhausted — return fallback
            return _LLM_FALLBACK_RESPONSE  # Module-level constant

_LLM_FALLBACK_RESPONSE = json.dumps({
    "verdict": "insufficient",
    "reason": "LLM temporarily unavailable",
    "fallback": True
})
```

---

## Resilience Metrics

```python
# metrics.py — Track resilience health
TOOL_RETRIES = Counter("hdtv_tool_retries_total", ["tool_name", "error_type"])
TOOL_TIMEOUTS = Counter("hdtv_tool_timeouts_total", ["tool_name"])
CONTEXT_TRUNCATIONS = Counter("hdtv_context_truncations_total", ["model"])
SANDBOX_EXECUTIONS = Counter("hdtv_sandbox_executions_total", ["type", "status"])
LLM_CIRCUIT_TRIPS = Counter("hdtv_llm_circuit_trips_total", ["backend", "role"])
```

**Alert rules liên quan:**
- `HdtvToolHighFailureRate`: Tool fail rate > 20% trong 5 phút
- `HdtvLlmCircuitOpen`: Circuit breaker OPEN > 5 phút
- `HdtvContextTruncationSpike`: Context truncation rate tăng đột biến
