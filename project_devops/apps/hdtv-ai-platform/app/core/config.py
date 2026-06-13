from functools import lru_cache
from pathlib import Path
from urllib.parse import quote_plus, urlparse, urlunparse

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _read_secret_file(file_path: str | None) -> str | None:
    """Read secret from file if provided, otherwise return None."""
    if file_path and Path(file_path).exists():
        return Path(file_path).read_text().strip()
    return None


def _build_database_url(
    base_url: str,
    password: str | None = None,
    password_file: str | None = None,
) -> str:
    """Build database URL, replacing password if provided or read from file."""
    # Try to get password from file first
    db_password = _read_secret_file(password_file) or password
    if not db_password:
        return base_url

    # Parse and rebuild URL with password
    parsed = urlparse(base_url)
    # Split netloc
    netloc_parts = parsed.netloc.split("@")
    if len(netloc_parts) == 1:
        # No password in base_url
        return base_url
    user_info, host_part = netloc_parts[0], netloc_parts[1]
    if ":" not in user_info:
        # No password in base_url
        return base_url
    # Split user:password
    username, _ = user_info.split(":", 1)
    new_user_info = f"{username}:{quote_plus(db_password)}"
    new_netloc = f"{new_user_info}@{host_part}"
    return urlunparse((
        parsed.scheme,
        new_netloc,
        parsed.path,
        parsed.params,
        parsed.query,
        parsed.fragment,
    ))


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "hdtv-ai-platform"
    debug: bool = False
    api_prefix: str = "/api/v1"
    cors_origins: str = "*"  # comma-separated list, or * for all (reads CORS_ORIGINS)

    # JWT auth
    jwt_secret: str = "hdtv-dev-secret-change-in-production"  # reads JWT_SECRET
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 480  # 8 hours

    # Public field — Pydantic reads DATABASE_URL env var (set by docker-compose).
    # Default uses 'postgres' hostname (standalone dev compose).
    # Platform compose overrides this with platform-postgres hostname.
    database_url: str = "postgresql+asyncpg://hdtv_user:changeme_hdtv@postgres:5432/hdtv_db"
    hdtv_postgres_password: str = ""
    hdtv_postgres_password_file: str = ""
    redis_url: str = "redis://redis:6379/0"
    celery_broker_url: str = "redis://redis:6379/1"
    celery_result_backend: str = "redis://redis:6379/2"

    @property
    def effective_database_url(self) -> str:
        """Database URL with password injected from secret file if available.

        Priority: HDTV_POSTGRES_PASSWORD_FILE > HDTV_POSTGRES_PASSWORD > password embedded in DATABASE_URL.
        """
        return _build_database_url(
            self.database_url,
            self.hdtv_postgres_password,
            self.hdtv_postgres_password_file,
        )

    # ==========================================================================
    # LLM — Ubuntu llama-server
    # ==========================================================================
    # Single source of truth: .env
    #   ACER_HOST=192.168.100.6   ← đổi IP ở đây, chỉ một chỗ duy nhất
    #   LLM_MODEL=gemma-4-2b-it
    #   LLM_TIMEOUT=120.0
    #   LLM_BASE_URL=             ← để trống → tự build http://<ACER_HOST>:8080/v1
    #                                hoặc set URL cụ thể để override hoàn toàn
    # ==========================================================================
    acer_host: str = ""        # reads ACER_HOST — bắt buộc có trong .env
    llm_base_url: str = ""     # reads LLM_BASE_URL — nếu trống thì derive từ acer_host
    llm_model: str = "gemma-4-2b-it"
    llm_timeout: float = 120.0

    @model_validator(mode="after")
    def _derive_llm_base_url(self) -> "Settings":
        """Derive llm_base_url từ acer_host nếu LLM_BASE_URL không set trong .env."""
        if not self.llm_base_url:
            if not self.acer_host:
                raise ValueError(
                    "Phải set ACER_HOST trong .env "
                    "(hoặc set LLM_BASE_URL trực tiếp)"
                )
            self.llm_base_url = f"http://{self.acer_host}:8080/v1"
        return self

    gemini_api_key: str = ""
    gemini_api_key_1: str = ""
    gemini_api_key_2: str = ""
    gemini_api_key_3: str = ""
    gemini_api_key_4: str = ""
    gemini_api_key_5: str = ""
    gemini_api_key_6: str = ""
    gemini_api_key_7: str = ""
    gemini_api_key_8: str = ""
    gemini_api_key_9: str = ""
    gemini_model: str = "gemini-2.5-flash"          # reads GEMINI_MODEL
    gemini_api_version: str = "v1beta"               # reads GEMINI_API_VERSION
    gemini_temperature: float = 0.2                  # reads GEMINI_TEMPERATURE
    gemini_max_tokens: int = 4096                    # reads GEMINI_MAX_TOKENS
    gemini_http_retries: int = 3                     # reads GEMINI_HTTP_RETRIES
    gemini_http_retry_backoff_s: float = 2.0         # reads GEMINI_HTTP_RETRY_BACKOFF_S

    chroma_host: str = "chroma"
    chroma_port: int = 8000

    minio_endpoint: str = "minio:9000"
    # minio_root_user / minio_root_password map .env keys used by docker-compose.
    # minio_access_key / minio_secret_key are the SDK-facing names — they alias the same values.
    minio_root_user: str = "hdtv_minio"       # reads MINIO_ROOT_USER from env
    minio_root_password: str = "changeme_minio"  # reads MINIO_ROOT_PASSWORD from env
    minio_root_password_file: str = ""          # reads MINIO_ROOT_PASSWORD_FILE from env
    minio_bucket: str = "dossiers"
    minio_secure: bool = False

    @property
    def minio_access_key(self) -> str:
        """Alias for MinIO SDK — maps MINIO_ROOT_USER."""
        return self.minio_root_user

    @property
    def minio_secret_key(self) -> str:
        """Alias for MinIO SDK — maps MINIO_ROOT_PASSWORD, or reads from file if available."""
        secret = _read_secret_file(self.minio_root_password_file)
        return secret or self.minio_root_password

    @property
    def meili_api_key(self) -> str:
        """Alias for Meilisearch SDK — maps MEILI_MASTER_KEY, or reads from file if available."""
        secret = _read_secret_file(self.meili_master_key_file)
        return secret or self.meili_master_key

    # T-11: Meilisearch full-text search
    meili_url: str = "http://hdtv-meilisearch:7700"
    meili_master_key: str = ""  # reads MEILI_MASTER_KEY from env
    meili_master_key_file: str = ""  # reads MEILI_MASTER_KEY_FILE from env
    meili_index_dossiers: str = "dossiers"

    # T-15: Vector Memory Service (Chroma HTTP client to existing chroma container)
    chroma_collection_memories: str = "agent_memories"
    chroma_collection_feedback_lessons: str = "feedback_lessons"
    memory_top_k: int = 5
    memory_embed_model: str = ""  # empty = no local embedding; Chroma uses its own embedder

    # Rate limiting (sliding window per IP, backed by Redis)
    rate_limit_enabled: bool = True
    rate_limit_window_s: int = 60
    rate_limit_appraise: int = 5    # POST **/appraise — heavy LLM operation
    rate_limit_upload: int = 10     # POST **/upload — file upload
    rate_limit_default: int = 120   # All other API endpoints

    # Context window management
    context_max_tokens: int = 0       # 0 = use model-specific limit from context_manager
    context_obs_max_tokens: int = 2048  # Max tokens for observation FIFO buffer

    # MCP Server
    mcp_api_key: str = ""  # empty = no auth required (set in production)
    mcp_api_key_file: str = ""

    @property
    def mcp_api_key_actual(self) -> str:
        secret = _read_secret_file(self.mcp_api_key_file)
        return secret or self.mcp_api_key

    # T-25: LLM Circuit Breaker
    llm_circuit_failure_threshold: int = 5   # failures in window before OPEN
    llm_circuit_window_s: int = 60           # sliding window size (seconds)
    llm_circuit_cooldown_s: int = 30         # cooldown before HALF_OPEN probe
    appraisal_max_duration_s: int = 300      # absolute timeout for full appraisal

    # T-26: Sandbox Docker executor
    sandbox_use_docker: bool = False         # False = process-level (safe default)
    sandbox_docker_image: str = "python:3.11-alpine"
    sandbox_docker_memory: str = "64m"
    sandbox_docker_timeout_s: int = 15

    # T-27: RAG ingestion pipeline
    rag_docs_dir: str = "/opt/rag-docs"
    rag_chunk_size_tokens: int = 512
    rag_chunk_overlap_tokens: int = 64
    rag_legal_collection: str = "legal_docs"
    rag_stale_days: int = 30

    # T-28: OTel Tracing (opt-in, disabled by default)
    tracing_enabled: bool = False
    jaeger_host: str = "platform-jaeger"
    jaeger_port: int = 4317

    # T-30: Execution Harness
    tool_execution_timeout_s: int = 30       # per-tool timeout (4× shorter than llm_timeout)
    tool_max_retries: int = 1                # retry count for transient errors
    tool_retry_backoff_s: float = 2.0        # backoff between retries

    @property
    def gemini_api_keys(self) -> list[str]:
        """Get all available Gemini API keys.

        Accepts both AIzaSy... (standard REST keys) and AQ.Ab8... (OAuth-style keys).
        Filters out empty strings only.
        """
        keys = []
        # Primary key
        if self.gemini_api_key and self.gemini_api_key.strip():
            keys.append(self.gemini_api_key.strip())
        # Numbered keys 1-9
        for i in range(1, 10):
            key = getattr(self, f"gemini_api_key_{i}", "").strip()
            if key:
                keys.append(key)
        # Deduplicate while preserving order
        return list(dict.fromkeys(keys))


@lru_cache
def get_settings() -> Settings:
    return Settings()
