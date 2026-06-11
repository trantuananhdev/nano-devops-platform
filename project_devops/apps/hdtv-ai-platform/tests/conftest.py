"""Pytest fixtures for offline static tests (T-45).

Mocks environment so imports work without Docker stack / live DB.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Ensure app package resolves when pytest is invoked from repo root.
_APP_ROOT = Path(__file__).resolve().parents[1]
if str(_APP_ROOT) not in sys.path:
    sys.path.insert(0, str(_APP_ROOT))

# Minimal env — avoid reading missing secret files during Settings init.
os.environ.setdefault("HDTV_POSTGRES_PASSWORD", "test_static")
os.environ.setdefault("REDIS_URL", "redis://127.0.0.1:6379/0")
os.environ.setdefault("CELERY_BROKER_URL", "redis://127.0.0.1:6379/1")
os.environ.setdefault("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/2")
os.environ.setdefault("LLM_BASE_URL", "http://127.0.0.1:8080/v1")
os.environ.setdefault("TRACING_ENABLED", "false")

import pytest


@pytest.fixture(autouse=True)
def _reset_settings_cache() -> None:
    """Clear lru_cache on get_settings between tests."""
    from app.core.config import get_settings

    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
