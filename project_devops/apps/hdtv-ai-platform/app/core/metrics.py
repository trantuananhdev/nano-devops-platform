"""
Prometheus metrics — HDTV AI Platform.

Expose /metrics endpoint cho Prometheus scrape.
Không dùng opentelemetry (tránh heavy deps trên Alpine).
Dùng pure prometheus_client — nhẹ, zero overhead.

Metrics được track:
  - http_requests_total           (counter)  — by method, endpoint, status
  - http_request_duration_seconds (histogram) — latency per endpoint
  - llm_calls_total               (counter)  — by role, backend, status
  - llm_tokens_estimated_total    (counter)  — estimated tokens consumed
  - tool_calls_total              (counter)  — by tool_name, status
  - tool_duration_seconds         (histogram) — tool execution latency
  - agent_plans_total             (counter)  — by verdict (sufficient/revise/escalate)
  - agent_critic_rejections_total (counter)
  - context_truncations_total     (counter)  — how often context was trimmed
  - rate_limit_hits_total         (counter)  — by endpoint
"""

from __future__ import annotations

try:
    from prometheus_client import (
        Counter,
        Histogram,
        CollectorRegistry,
        generate_latest,
        CONTENT_TYPE_LATEST,
        REGISTRY,
    )
    _PROMETHEUS_AVAILABLE = True
except ImportError:
    _PROMETHEUS_AVAILABLE = False

import logging

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Registry (use default REGISTRY so /metrics works with generate_latest)
# ---------------------------------------------------------------------------

if _PROMETHEUS_AVAILABLE:
    # HTTP metrics
    HTTP_REQUESTS = Counter(
        "hdtv_http_requests_total",
        "Total HTTP requests",
        ["method", "endpoint", "status_code"],
    )
    HTTP_DURATION = Histogram(
        "hdtv_http_request_duration_seconds",
        "HTTP request latency",
        ["endpoint"],
        buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0],
    )

    # LLM metrics
    LLM_CALLS = Counter(
        "hdtv_llm_calls_total",
        "Total LLM API calls",
        ["role", "backend", "status"],
    )
    LLM_TOKENS = Counter(
        "hdtv_llm_tokens_estimated_total",
        "Estimated tokens sent to LLM",
        ["role", "backend"],
    )

    # Tool metrics
    TOOL_CALLS = Counter(
        "hdtv_tool_calls_total",
        "Total agent tool calls",
        ["tool_name", "status"],
    )
    TOOL_DURATION = Histogram(
        "hdtv_tool_duration_seconds",
        "Tool execution latency",
        ["tool_name"],
        buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.0, 5.0, 15.0, 30.0],
    )

    # Agent lifecycle
    AGENT_PLANS = Counter(
        "hdtv_agent_plans_total",
        "Agent plan outcomes",
        ["verdict"],  # sufficient / revise / escalate
    )
    CRITIC_REJECTIONS = Counter(
        "hdtv_agent_critic_rejections_total",
        "Times critic rejected a draft report",
    )

    # Context management
    CONTEXT_TRUNCATIONS = Counter(
        "hdtv_context_truncations_total",
        "Times message list was trimmed to fit context window",
        ["model"],
    )

    # Rate limiting
    RATE_LIMIT_HITS = Counter(
        "hdtv_rate_limit_hits_total",
        "Rate limit rejections",
        ["endpoint"],
    )

    # T-25: Circuit breaker + appraisal timeout
    LLM_CIRCUIT_TRIPS = Counter(
        "hdtv_llm_circuit_trips_total",
        "Times LLM circuit breaker tripped to OPEN",
        ["backend", "role"],
    )
    APPRAISAL_TIMEOUTS = Counter(
        "hdtv_appraisal_timeouts_total",
        "Times appraisal task exceeded max_duration",
    )

    # T-26: Sandbox execution
    SANDBOX_EXECUTIONS = Counter(
        "hdtv_sandbox_executions_total",
        "Sandbox command executions",
        ["type", "status"],   # type=shell|python, status=success|blocked|timeout|error
    )

    # T-30: Execution harness
    TOOL_RETRIES = Counter(
        "hdtv_tool_retries_total",
        "Tool calls retried due to transient errors",
        ["tool_name", "error_type"],
    )
    TOOL_TIMEOUTS = Counter(
        "hdtv_tool_timeouts_total",
        "Tool calls that exceeded per-tool timeout",
        ["tool_name"],
    )
    TOOL_INPUT_VALIDATION_ERRORS = Counter(
        "hdtv_tool_input_validation_errors_total",
        "Tool calls rejected due to invalid input schema",
        ["tool_name"],
    )
else:
    logger.warning("prometheus_client not installed — metrics disabled (pip install prometheus-client)")

    # Stub objects so callers don't need try/except
    class _NoOpMetric:
        def labels(self, **kw):  # noqa: ANN001
            return self
        def inc(self, amount: float = 1) -> None:  # noqa: ANN001
            pass
        def observe(self, value: float) -> None:  # noqa: ANN001
            pass

    _noop = _NoOpMetric()
    HTTP_REQUESTS    = _noop  # type: ignore[assignment]
    HTTP_DURATION    = _noop  # type: ignore[assignment]
    LLM_CALLS        = _noop  # type: ignore[assignment]
    LLM_TOKENS       = _noop  # type: ignore[assignment]
    TOOL_CALLS       = _noop  # type: ignore[assignment]
    TOOL_DURATION    = _noop  # type: ignore[assignment]
    AGENT_PLANS      = _noop  # type: ignore[assignment]
    CRITIC_REJECTIONS= _noop  # type: ignore[assignment]
    CONTEXT_TRUNCATIONS = _noop  # type: ignore[assignment]
    RATE_LIMIT_HITS  = _noop  # type: ignore[assignment]
    LLM_CIRCUIT_TRIPS = _noop  # type: ignore[assignment]
    APPRAISAL_TIMEOUTS = _noop  # type: ignore[assignment]
    SANDBOX_EXECUTIONS = _noop  # type: ignore[assignment]
    TOOL_RETRIES     = _noop  # type: ignore[assignment]
    TOOL_TIMEOUTS    = _noop  # type: ignore[assignment]
    TOOL_INPUT_VALIDATION_ERRORS = _noop  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Helper: get latest metrics bytes for /metrics endpoint
# ---------------------------------------------------------------------------

def get_metrics_output() -> tuple[bytes, str]:
    """Return (metrics_bytes, content_type) for Prometheus scrape endpoint."""
    if not _PROMETHEUS_AVAILABLE:
        return b"# prometheus_client not installed\n", "text/plain"
    return generate_latest(REGISTRY), CONTENT_TYPE_LATEST
