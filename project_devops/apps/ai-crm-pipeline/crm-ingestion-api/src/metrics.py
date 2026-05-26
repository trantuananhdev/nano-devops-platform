"""Prometheus metrics for crm-ingestion-api."""

from prometheus_client import Counter, Histogram

INGEST_REQUESTS = Counter(
    "crm_ingest_requests_total",
    "Webhook requests received",
    ["channel", "status"],
)

INGEST_ERRORS = Counter(
    "crm_ingest_errors_total",
    "Ingestion errors by type",
    ["error_type"],
)

ENQUEUE_DURATION = Histogram(
    "crm_ingest_enqueue_duration_seconds",
    "Time to validate and enqueue a job",
    ["channel"],
)
