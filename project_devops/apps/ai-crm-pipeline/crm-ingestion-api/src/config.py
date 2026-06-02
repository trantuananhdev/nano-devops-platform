"""Runtime configuration from environment."""

import os

VERSION = "1.0.0"
PORT = int(os.getenv("PORT", "8080"))

REDIS_URL = os.getenv("REDIS_URL", "redis://platform-redis:6379/0")
QUEUE_KEY = os.getenv("CRM_QUEUE_KEY", "crm:queue:messages")
DEDUP_PREFIX = os.getenv("CRM_DEDUP_PREFIX", "crm:dedup:")
DEDUP_TTL_SECONDS = int(os.getenv("CRM_DEDUP_TTL_SECONDS", "86400"))
MAX_QUEUE_LENGTH = int(os.getenv("CRM_MAX_QUEUE_LENGTH", "10000"))

CRM_WEBHOOK_SECRET = os.getenv("CRM_WEBHOOK_SECRET", "").strip()

# Same LLM stack as ai-powered-development/ai-agent (Gemini 2.5 Flash via worker)
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_VERSION = os.getenv("GEMINI_API_VERSION", "v1beta")
AGENTIC_AI_URL = os.getenv("AGENTIC_AI_URL", "http://platform-agentic-ai:3000")
CRM_WORKER_SERVICE = os.getenv("CRM_WORKER_SERVICE", "platform-crm-worker")

EVENTS_CHANNEL = os.getenv("CRM_EVENTS_CHANNEL", "crm:events:leads")
CRM_DEMO_API_KEY = os.getenv("CRM_DEMO_API_KEY", "").strip()
CORS_ORIGINS = [
    o.strip()
    for o in os.getenv(
        "CORS_ORIGINS",
        "https://crm-demo.nano.platform,http://localhost:5173",
    ).split(",")
    if o.strip()
]


def _database_url() -> str:
    url = os.getenv("CRM_DATABASE_URL", "").strip()
    if url:
        return url
    host = os.getenv("POSTGRES_HOST", "platform-postgres")
    db = os.getenv("CRM_POSTGRES_DB", "crm_db")
    user = os.getenv("CRM_POSTGRES_USER", "crm_user")
    password = os.getenv("CRM_DB_PASSWORD", "devadmin")
    return f"postgresql://{user}:{password}@{host}:5432/{db}"


DATABASE_URL = _database_url()

# Mặc định bật: demo dùng rule-based, không đốt quota Gemini (~5 req/ngày free tier)
CRM_SKIP_GEMINI = os.getenv("CRM_SKIP_GEMINI", "true").lower() == "true"
DEMO_BURST_MAX_MESSAGES = int(os.getenv("DEMO_BURST_MAX_MESSAGES", "3"))
