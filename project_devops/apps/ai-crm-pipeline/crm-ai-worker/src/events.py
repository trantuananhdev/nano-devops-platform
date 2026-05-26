"""Redis Pub/Sub events for CRM demo SSE stream."""

from __future__ import annotations

import json
import logging
from typing import Any

import redis

from config import EVENTS_CHANNEL, REDIS_URL

logger = logging.getLogger(__name__)


def publish_lead_event(lead: dict[str, Any], event_type: str = "lead_processed") -> None:
    payload = {
        "type": event_type,
        "message_id": lead.get("message_id"),
        "channel": lead.get("channel"),
        "raw_text": lead.get("raw_text"),
        "customer_name": lead.get("customer_name"),
        "phone": lead.get("phone"),
        "product_interest": lead.get("product_interest"),
        "language": lead.get("language"),
        "order_id": lead.get("order_id"),
        "shop_id": lead.get("shop_id"),
        "locale": lead.get("locale"),
        "urgency": lead.get("urgency"),
        "sentiment": lead.get("sentiment"),
        "intent": lead.get("intent"),
        "alert_sent": lead.get("alert_sent", False),
        "alert_type": lead.get("alert_type"),
        "auto_reply_sent": lead.get("auto_reply_sent", False),
        "summary": lead.get("summary"),
        "auto_reply_content": lead.get("auto_reply_content"),
        "processed_at": lead.get("processed_at"),
    }
    try:
        r = redis.from_url(REDIS_URL, decode_responses=True)
        r.publish(EVENTS_CHANNEL, json.dumps(payload))
        r.close()
    except Exception as exc:
        logger.warning("Failed to publish lead event: %s", exc)
