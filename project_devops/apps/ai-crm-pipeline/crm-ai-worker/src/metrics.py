from prometheus_client import Counter, Gauge, Histogram, start_http_server

QUEUE_DEPTH = Gauge("crm_queue_depth", "Messages waiting in Redis queue")
JOBS_PROCESSED = Counter(
    "crm_worker_jobs_processed_total",
    "Jobs processed by outcome",
    ["status"],
)
LLM_LATENCY = Histogram("crm_llm_latency_seconds", "Gemini API round-trip seconds")
ALERTS_SENT = Counter("crm_alerts_sent_total", "Alerts dispatched", ["alert_type"])
AUTO_REPLY_TOTAL = Counter(
    "crm_auto_reply_total",
    "Auto-replies sent or skipped",
    ["status"],
)


def start_metrics_server(port: int) -> None:
    start_http_server(port)
