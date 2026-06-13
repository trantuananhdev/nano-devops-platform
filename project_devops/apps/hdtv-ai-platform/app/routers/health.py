import asyncio

import httpx
import redis.asyncio as aioredis
from fastapi import APIRouter
from sqlalchemy import text

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.schemas.dossier import HealthOut

router = APIRouter()

_TIMEOUT = 3.0   # seconds per dependency probe


async def _check_postgres() -> str:
    try:
        async with async_session_factory() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:
        return f"error: {str(exc)[:120]}"


async def _check_redis(redis_url: str) -> str:
    try:
        r = aioredis.from_url(redis_url, socket_connect_timeout=2, socket_timeout=2)
        await r.ping()
        await r.aclose()
        return "ok"
    except Exception as exc:
        return f"error: {str(exc)[:120]}"


async def _check_http(url: str) -> str:
    try:
        async with httpx.AsyncClient(timeout=_TIMEOUT) as client:
            resp = await client.get(url)
        return "ok" if resp.status_code < 400 else f"http {resp.status_code}"
    except Exception as exc:
        return f"error: {str(exc)[:120]}"


@router.get("/health", response_model=HealthOut)
async def health() -> HealthOut:
    settings = get_settings()

    # LLM base url looks like http://host:8080/v1 — health lives at http://host:8080/health
    llm_health_url = settings.llm_base_url.rstrip("/").removesuffix("/v1") + "/health"
    chroma_url = f"http://{settings.chroma_host}:{settings.chroma_port}/api/v1/heartbeat"
    minio_proto = "https" if settings.minio_secure else "http"
    minio_url = f"{minio_proto}://{settings.minio_endpoint}/minio/health/live"

    results: list[tuple[str, str]] = await asyncio.gather(
        asyncio.ensure_future(_check_postgres()),
        asyncio.ensure_future(_check_redis(settings.redis_url)),
        asyncio.ensure_future(_check_http(llm_health_url)),
        asyncio.ensure_future(_check_http(chroma_url)),
        asyncio.ensure_future(_check_http(f"{settings.meili_url}/health")),
        asyncio.ensure_future(_check_http(minio_url)),
        return_exceptions=False,
    )

    keys = ["postgres", "redis", "llm", "chroma", "meilisearch", "minio"]
    checks = dict(zip(keys, results))

    degraded = [k for k, v in checks.items() if v != "ok"]
    status = "degraded" if degraded else "ok"

    return HealthOut(status=status, checks=checks)
