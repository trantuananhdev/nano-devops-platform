"""Redis Pub/Sub events for CRM demo SSE stream (ingestion side)."""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as redis

from config import EVENTS_CHANNEL, REDIS_URL

logger = logging.getLogger(__name__)


async def publish_lead_event_async(r: redis.Redis, payload: dict[str, Any]) -> None:
    try:
        await r.publish(EVENTS_CHANNEL, json.dumps(payload))
    except Exception as exc:
        logger.warning("Failed to publish lead event: %s", exc)


def build_queued_event(job: dict[str, Any], channel: str, queue_depth: int) -> dict[str, Any]:
    payload = job.get("payload") or {}
    return {
        "type": "lead_queued",
        "message_id": job["message_id"],
        "channel": channel,
        "raw_text": payload.get("raw_text", ""),
        "customer_name": payload.get("customer_name"),
        "phone": payload.get("phone"),
        "order_id": payload.get("order_id"),
        "shop_id": payload.get("shop_id"),
        "locale": payload.get("locale"),
        "urgency": "pending",
        "sentiment": "pending",
        "intent": "queued",
        "summary": "Đã tiếp nhận — AI đang xếp hàng xử lý",
        "alert_sent": False,
        "auto_reply_sent": False,
        "queue_depth": queue_depth,
        "received_at": job.get("received_at"),
    }
