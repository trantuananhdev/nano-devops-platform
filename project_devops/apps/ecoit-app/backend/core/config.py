"""Core configuration — reads from environment variables."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App
    APP_NAME: str = "ecoit-app"
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    LOG_LEVEL: str = "info"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ecoit_user:changeme@localhost:5432/ecoit_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security
    JWT_SECRET: str = "changeme-jwt-secret-32chars-minimum"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    ADMIN_API_KEY: str = "changeme-admin-key"

    # CORS — comma-separated list
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    # AI (optional)
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    # Observability
    METRICS_PORT: int = 9100


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
