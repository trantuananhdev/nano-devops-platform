"""
crm-ingestion-api — zero-blocking webhook ingestion for AI CRM pipeline.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from typing import Any, Optional

import redis.asyncio as redis
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from api_read import router as read_router
from config import (
    AGENTIC_AI_URL,
    CORS_ORIGINS,
    CRM_WEBHOOK_SECRET,
    CRM_WORKER_SERVICE,
    DEDUP_PREFIX,
    DEDUP_TTL_SECONDS,
    GEMINI_API_VERSION,
    GEMINI_MODEL,
    LLM_PROVIDER,
    MAX_QUEUE_LENGTH,
    QUEUE_KEY,
    REDIS_URL,
    VERSION,
)
from events import build_queued_event, publish_lead_event_async
from metrics import ENQUEUE_DURATION, INGEST_ERRORS, INGEST_REQUESTS

app = FastAPI(title="CRM Ingestion API", version=VERSION)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(read_router)

_redis: Optional[redis.Redis] = None

ALLOWED_CHANNELS = frozenset({"facebook", "tiktok", "zalo", "instagram", "shopee", "generic"})


class WebhookBody(BaseModel):
    message_id: str = Field(..., min_length=1, max_length=128)
    raw_text: str = Field(..., min_length=1)
    channel: Optional[str] = None
    sender_id: Optional[str] = None
    page_id: Optional[str] = None
    shop_id: Optional[str] = None
    order_id: Optional[str] = None
    timestamp: Optional[str] = None
    locale: Optional[str] = None
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    metadata: Optional[dict[str, Any]] = None

    model_config = {"extra": "allow"}


async def get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        _redis = redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def verify_secret(x_webhook_secret: Optional[str]) -> None:
    if not CRM_WEBHOOK_SECRET:
        return
    if x_webhook_secret != CRM_WEBHOOK_SECRET:
        INGEST_ERRORS.labels(error_type="unauthorized").inc()
        raise HTTPException(
            status_code=401,
            detail={"status": "error", "code": "unauthorized", "detail": "Invalid X-Webhook-Secret"},
        )


async def is_duplicate(r: redis.Redis, message_id: str) -> bool:
    return bool(await r.exists(f"{DEDUP_PREFIX}{message_id}"))


async def mark_dedup(r: redis.Redis, message_id: str) -> None:
    await r.set(f"{DEDUP_PREFIX}{message_id}", "1", ex=DEDUP_TTL_SECONDS)


def build_job(body: WebhookBody, channel: str) -> dict[str, Any]:
    payload = body.model_dump()
    payload["channel"] = channel
    return {
        "job_id": body.message_id,
        "message_id": body.message_id,
        "channel": channel,
        "received_at": utc_now_iso(),
        "payload": payload,
    }


async def enqueue_message(r: redis.Redis, job: dict[str, Any], channel: str) -> dict[str, Any]:
    queue_len = await r.llen(QUEUE_KEY)
    if queue_len >= MAX_QUEUE_LENGTH:
        INGEST_ERRORS.labels(error_type="queue_full").inc()
        INGEST_REQUESTS.labels(channel=channel, status="rejected").inc()
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "code": "queue_unavailable",
                "detail": f"Queue at capacity ({MAX_QUEUE_LENGTH})",
            },
        )

    await r.lpush(QUEUE_KEY, json.dumps(job))
    await mark_dedup(r, job["message_id"])
    queue_depth = await r.llen(QUEUE_KEY)
    await publish_lead_event_async(r, build_queued_event(job, channel, queue_depth))
    queued_at = utc_now_iso()
    return {
        "status": "accepted",
        "job_id": job["job_id"],
        "message_id": job["message_id"],
        "queued_at": queued_at,
        "queue_depth": queue_depth,
    }


@app.on_event("shutdown")
async def shutdown() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


@app.get("/health")
async def health() -> JSONResponse:
    try:
        r = await get_redis()
        await r.ping()
        return JSONResponse(
            content={
                "status": "healthy",
                "redis": "up",
                "version": VERSION,
                "pipeline": {
                    "ingestion": "crm-ingestion-api",
                    "worker": CRM_WORKER_SERVICE,
                    "llm_provider": LLM_PROVIDER,
                    "llm_model": GEMINI_MODEL,
                    "llm_api_version": GEMINI_API_VERSION,
                    "platform_ai_service": AGENTIC_AI_URL,
                    "note": "LLM calls use same Gemini REST stack as ai-powered-development/ai-agent",
                },
            },
        )
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "redis": "down", "version": VERSION},
        )


@app.get("/metrics")
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/webhook/facebook")
async def webhook_facebook(
    body: WebhookBody,
    request: Request,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
) -> dict[str, Any]:
    return await handle_webhook("facebook", body, x_webhook_secret)


@app.post("/webhook/tiktok")
async def webhook_tiktok(
    body: WebhookBody,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
) -> dict[str, Any]:
    return await handle_webhook("tiktok", body, x_webhook_secret)


@app.post("/webhook/generic")
async def webhook_generic(
    body: WebhookBody,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
) -> dict[str, Any]:
    return await handle_webhook("generic", body, x_webhook_secret)


@app.post("/webhook/shopee")
async def webhook_shopee(
    body: WebhookBody,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
) -> dict[str, Any]:
    return await handle_webhook("shopee", body, x_webhook_secret)


@app.post("/webhook/zalo")
async def webhook_zalo(
    body: WebhookBody,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
) -> dict[str, Any]:
    """Zalo OA webhook — nhận tin nhắn từ Zalo Official Account (BDS)."""
    return await handle_webhook("zalo", body, x_webhook_secret)


@app.post("/webhook/instagram")
async def webhook_instagram(
    body: WebhookBody,
    x_webhook_secret: Optional[str] = Header(None, alias="X-Webhook-Secret"),
) -> dict[str, Any]:
    """Instagram DM webhook — nhận tin nhắn Direct Message (BDS)."""
    return await handle_webhook("instagram", body, x_webhook_secret)


async def handle_webhook(
    channel: str,
    body: WebhookBody,
    x_webhook_secret: Optional[str],
) -> dict[str, Any]:
    if channel not in ALLOWED_CHANNELS:
        raise HTTPException(status_code=400, detail="Unknown channel")

    verify_secret(x_webhook_secret)
    start = time.perf_counter()

    try:
        r = await get_redis()
    except Exception as exc:
        INGEST_ERRORS.labels(error_type="redis_connect").inc()
        INGEST_REQUESTS.labels(channel=channel, status="error").inc()
        raise HTTPException(
            status_code=503,
            detail={
                "status": "error",
                "code": "queue_unavailable",
                "detail": str(exc),
            },
        ) from exc

    try:
        if await is_duplicate(r, body.message_id):
            INGEST_REQUESTS.labels(channel=channel, status="duplicate").inc()
            ENQUEUE_DURATION.labels(channel=channel).observe(time.perf_counter() - start)
            return {
                "status": "accepted",
                "job_id": body.message_id,
                "queued_at": utc_now_iso(),
                "duplicate": True,
            }

        job = build_job(body, channel)
        result = await enqueue_message(r, job, channel)
        INGEST_REQUESTS.labels(channel=channel, status="accepted").inc()
        ENQUEUE_DURATION.labels(channel=channel).observe(time.perf_counter() - start)
        return result

    except HTTPException:
        raise
    except Exception as exc:
        INGEST_ERRORS.labels(error_type="internal").inc()
        INGEST_REQUESTS.labels(channel=channel, status="error").inc()
        raise HTTPException(
            status_code=500,
            detail={"status": "error", "code": "internal_error", "detail": str(exc)},
        ) from exc


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    if isinstance(exc.detail, dict):
        return JSONResponse(status_code=exc.status_code, content=exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "code": "error", "detail": exc.detail},
    )
