import os
import itertools

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


def _load_gemini_keys() -> list[str]:
    """Load Gemini API keys from environment variables (supports 1..9)."""
    keys = []
    # Load numbered keys (1-9)
    for i in range(1, 10):
        key = os.getenv(f"GEMINI_API_KEY_{i}", "").strip().strip('"').strip("'")
        if key:
            keys.append(key)
    # Fall back to single key
    if not keys:
        key = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")
        if key:
            keys.append(key)
    return keys


GEMINI_API_KEYS = _load_gemini_keys()
# Key rotation iterator (fallback when no fixed agent key)
_key_cycle = itertools.cycle(GEMINI_API_KEYS) if GEMINI_API_KEYS else None


def get_next_gemini_key() -> str:
    """Get the next Gemini API key in rotation."""
    if not _key_cycle:
        raise ValueError("No Gemini API keys available")
    return next(_key_cycle)


def get_agent_key(index: int) -> str:
    """Dedicated key for agent index 0..N (maps to GEMINI_API_KEY_1..9)."""
    if GEMINI_API_KEYS and index < len(GEMINI_API_KEYS):
        return GEMINI_API_KEYS[index]
    if GEMINI_API_KEYS:
        return GEMINI_API_KEYS[index % len(GEMINI_API_KEYS)]
    return get_next_gemini_key()


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
# Skip all Gemini calls (rule-based demo) — use when API quota is very low
CRM_SKIP_GEMINI = os.getenv("CRM_SKIP_GEMINI", "true").lower() == "true"
DEMO_BURST_MAX_MESSAGES = int(os.getenv("DEMO_BURST_MAX_MESSAGES", "3"))
CRM_WORKER_JOB_DELAY_MS = int(os.getenv("CRM_WORKER_JOB_DELAY_MS", "1200"))
EVENTS_CHANNEL = os.getenv("CRM_EVENTS_CHANNEL", "crm:events:leads")
