# Observability — Metrics, Logs, Traces, Alerts

> **Audience:** CTO, SRE
> **Mục đích:** Full observability stack — không chỉ infrastructure mà còn LLMOps-specific metrics.

---

## Observability Stack

```
┌─────────────────────────────────────────────────────────────────┐
│  METRICS: Prometheus + Grafana                                  │
│  • Application metrics (FastAPI, Celery)                        │
│  • LLMOps metrics (LLM calls, circuit breaker, tool execution)  │
│  • Infrastructure metrics (node-exporter, Docker SD)            │
│  • Custom HDTV metrics (appraisal throughput, risk distribution) │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  LOGS: Loki + Promtail                                          │
│  • Structured JSON logs từ FastAPI + Celery                     │
│  • Promtail collect từ Docker container logs                    │
│  • Correlate với trace ID (khi tracing enabled)                 │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  TRACES: Jaeger (opt-in)                                        │
│  • OpenTelemetry SDK (OTLP gRPC → Jaeger)                       │
│  • FastAPI auto-instrumentation                                 │
│  • Disabled by default (settings.tracing_enabled = False)       │
└─────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────┐
│  ALERTS: Prometheus Alertmanager                                │
│  • 14 alert rules (HDTV-specific)                               │
│  • Telegram / Email routing (configurable)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Custom HDTV Metrics

```python
# metrics.py — Domain-specific metrics
from prometheus_client import Counter, Histogram, Gauge

# LLM Health
LLM_CALLS = Counter("hdtv_llm_calls_total",
    ["backend", "role", "status"])
LLM_LATENCY = Histogram("hdtv_llm_latency_seconds",
    ["backend", "role"], buckets=[1, 5, 10, 30, 60])
LLM_CIRCUIT_TRIPS = Counter("hdtv_llm_circuit_trips_total",
    ["backend", "role"])

# Agent Loop
APPRAISAL_DURATION = Histogram("hdtv_appraisal_duration_seconds",
    buckets=[10, 30, 60, 120, 300])
APPRAISAL_TIMEOUTS = Counter("hdtv_appraisal_timeouts_total")
PLAN_REVISIONS = Counter("hdtv_plan_revisions_total")
CRITIC_REJECTIONS = Counter("hdtv_critic_rejections_total")

# Tool Execution
TOOL_CALLS = Counter("hdtv_tool_calls_total", ["tool_name", "status"])
TOOL_RETRIES = Counter("hdtv_tool_retries_total", ["tool_name", "error_type"])
TOOL_TIMEOUTS = Counter("hdtv_tool_timeouts_total", ["tool_name"])
TOOL_INPUT_VALIDATION_ERRORS = Counter("hdtv_tool_input_validation_errors_total",
    ["tool_name"])

# RAG/Memory
CONTEXT_TRUNCATIONS = Counter("hdtv_context_truncations_total", ["model"])
MEMORY_RETRIEVALS = Counter("hdtv_memory_retrievals_total", ["layer"])

# Sandbox
SANDBOX_EXECUTIONS = Counter("hdtv_sandbox_executions_total",
    ["type", "status"])  # type=shell|python, status=success|blocked|timeout
```

---

## Grafana Dashboard: HDTV Agent Intelligence

5-row dashboard hiển thị health của toàn bộ AI pipeline:

```
┌─────────────────────────────────────────────────────────┐
│  Row 1: LLM Health                                      │
│  • LLM call rate (req/s) per backend                    │
│  • LLM latency P50/P95/P99 per role                     │
│  • Circuit breaker state (CLOSED/OPEN/HALF_OPEN)        │
│  • Gemini key rotation events                           │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  Row 2: Agent Loop                                      │
│  • Appraisal throughput (appraisals/hour)               │
│  • Appraisal duration distribution (histogram)          │
│  • Plan revision rate (%)                               │
│  • Critic rejection rate (%)                            │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  Row 3: Tool Execution                                  │
│  • Tool call rate per tool name                         │
│  • Tool error rate per tool + error type                │
│  • Tool retry rate                                      │
│  • Tool timeout rate                                    │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  Row 4: RAG/Memory                                      │
│  • Context truncation rate (token overflow events)      │
│  • Memory retrieval count                               │
│  • Chroma collection size                               │
│  • RAG ingestion events (every 6h beat)                 │
└─────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────┐
│  Row 5: Infrastructure                                  │
│  • Node CPU/RAM (Ubuntu + Alpine)                       │
│  • Docker container resource usage                      │
│  • API error rate (5xx)                                 │
│  • WebSocket connection count                           │
└─────────────────────────────────────────────────────────┘
```

---

## 14 Alert Rules (hdtv-alerts.yml)

| Alert | Condition | Severity | Action |
|-------|-----------|----------|--------|
| `HdtvApiDown` | FastAPI health check fail 2 phút | **critical** | PagerDuty |
| `HdtvLlmCircuitOpen` | LLM circuit OPEN > 5 phút | **critical** | On-call |
| `HdtvAgentInfiniteLoop` | Appraisal duration > 5 phút | **warning** | Investigate |
| `HdtvToolHighFailureRate` | Tool fail rate > 20% | **warning** | Check tool |
| `HdtvAppraisalTimeout` | Timeout rate > 10% | **warning** | LLM check |
| `HdtvSandboxHighBlockRate` | Sandbox block rate > 30% | **warning** | Security |
| `HdtvContextTruncationSpike` | Truncation rate tăng 2x | **warning** | Model check |
| `HdtvHighRiskSpike` | HIGH risk rate > 50% | **info** | Business review |
| `HdtvFeedbackNegativeSpike` | Negative feedback > 30% | **warning** | Quality |
| `HdtvMemoryRetrievalZero` | Memory retrieval = 0 | **warning** | Chroma check |
| `HdtvMcpHighErrorRate` | MCP error rate > 10% | **warning** | MCP check |
| `HdtvCeleryWorkerDown` | No worker heartbeat 5 phút | **critical** | Restart worker |
| `HdtvDiskSpaceHigh` | Disk > 80% | **warning** | Cleanup |
| `HdtvRamPressure` | RAM > 85% | **warning** | Scale or optimize |

---

## Audit Log — Business-level Observability

Ngoài technical metrics, có audit trail cho compliance:

```
ai_audit_logs:
  - task_id, tool_name, plan_step_id
  - inputs (masked), outputs (masked)
  - execution_ms, error_type
  - created_at

mcp_call_logs:
  - tool_name, api_key_prefix (không lưu raw key)
  - is_streaming, execution_ms
  - is_error, output_incomplete
  - created_at
```

**Admin dashboard** có thể filter, search, export audit logs.
**Retention:** Không tự xóa (compliance), cần policy riêng.

---

## Tracing (OpenTelemetry — opt-in)

```python
# tracing.py — lazy import, không affect startup nếu disabled
def configure_tracer(app: FastAPI):
    if not settings.tracing_enabled:
        return  # No-op

    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

    provider = TracerProvider()
    exporter = OTLPSpanExporter(
        endpoint="http://platform-jaeger:4317",  # gRPC
    )
    # ...
    FastAPIInstrumentor.instrument_app(app)
```

**Enable:** `TRACING_ENABLED=true` trong `.env` → Jaeger nhận spans.
**Default off:** Tránh overhead khi không cần.
