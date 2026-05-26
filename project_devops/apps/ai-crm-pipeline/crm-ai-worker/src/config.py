import os

# Aligned with ai-powered-development/ai-agent/src/system/env.js + geminiProvider.js
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
REDIS_URL = os.getenv("REDIS_URL", "redis://platform-redis:6379/0")
QUEUE_KEY = os.getenv("CRM_QUEUE_KEY", "crm:queue:messages")
DLQ_KEY = os.getenv("CRM_DLQ_KEY", "crm:queue:dlq")
MAX_RETRIES = int(os.getenv("CRM_MAX_RETRIES", "3"))

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
GEMINI_API_VERSION = os.getenv("GEMINI_API_VERSION", "v1beta")
GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))
GEMINI_MAX_TOKENS = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))
GEMINI_TIMEOUT_MS = int(os.getenv("GEMINI_TIMEOUT_MS", "60000"))


def _load_gemini_key() -> str:
    """Key from repo root .env via docker compose env_file / cli.sh --env-file."""
    key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
    if key:
        return key
    key_file = os.getenv("GEMINI_API_KEY_FILE", "")
    if key_file and os.path.exists(key_file):
        with open(key_file, encoding="utf-8") as f:
            return f.read().strip()
    return ""


GEMINI_API_KEY = _load_gemini_key()


def _database_url() -> str:
    url = os.getenv("CRM_DATABASE_URL", "")
    if url:
        return url
    host = os.getenv("POSTGRES_HOST", "platform-postgres")
    db = os.getenv("CRM_POSTGRES_DB", "crm_db")
    user = os.getenv("CRM_POSTGRES_USER", "crm_user")
    password_file = os.getenv("CRM_DB_PASSWORD_FILE", "/run/secrets/crm_db_password")
    if os.path.exists(password_file):
        with open(password_file, encoding="utf-8") as f:
            password = f.read().strip()
    else:
        password = os.getenv("CRM_DB_PASSWORD", "devadmin")
    return f"postgresql://{user}:{password}@{host}:5432/{db}"


DATABASE_URL = _database_url()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
LARK_WEBHOOK_URL = os.getenv("LARK_WEBHOOK_URL", "")
ALERT_ENABLED = os.getenv("ALERT_ENABLED", "true").lower() == "true"
ALERT_COOLDOWN_SECONDS = int(os.getenv("ALERT_COOLDOWN_SECONDS", "60"))
ALERT_COOLDOWN_PREFIX = "crm:alert:cooldown:"

METRICS_PORT = int(os.getenv("METRICS_PORT", "9100"))
AGENTIC_AI_URL = os.getenv("AGENTIC_AI_URL", "http://platform-agentic-ai:3000")

AUTO_REPLY_ENABLED = os.getenv("AUTO_REPLY_ENABLED", "true").lower() == "true"
CRM_DEMO_LLM_FALLBACK = os.getenv("CRM_DEMO_LLM_FALLBACK", "true").lower() == "true"
CRM_WORKER_JOB_DELAY_MS = int(os.getenv("CRM_WORKER_JOB_DELAY_MS", "1200"))
EVENTS_CHANNEL = os.getenv("CRM_EVENTS_CHANNEL", "crm:events:leads")
