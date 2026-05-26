"""Alert dispatch per docs/ALERT_RULES.md."""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx
import redis.asyncio as redis

from config import (
    ALERT_COOLDOWN_PREFIX,
    ALERT_COOLDOWN_SECONDS,
    ALERT_ENABLED,
    LARK_WEBHOOK_URL,
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHAT_ID,
)
from metrics import ALERTS_SENT

logger = logging.getLogger(__name__)


def evaluate_alert_type(lead: dict[str, Any]) -> Optional[str]:
    intent = lead.get("intent")
    urgency = lead.get("urgency")
    sentiment = lead.get("sentiment")

    if intent == "cancel_order":
        return "cancel_intent"
    if urgency in ("high", "critical"):
        return "hot_lead"
    if sentiment == "negative":
        return "negative_sentiment"
    if intent == "complaint" and sentiment == "negative":
        return "complaint_escalation"
    return None


def format_message(alert_type: str, lead: dict[str, Any]) -> str:
    prefix = "⚠️ CANCEL RISK — " if alert_type == "cancel_intent" else ""
    return (
        f"{prefix}🚨 CRM Alert — {alert_type}\n"
        f"Channel: {lead.get('channel')}\n"
        f"Urgency: {lead.get('urgency')} | Sentiment: {lead.get('sentiment')}\n"
        f"Intent: {lead.get('intent')}\n"
        f"Customer: {lead.get('customer_name')} | Phone: {lead.get('phone')}\n"
        f"Product: {lead.get('product_interest')}\n"
        f"Summary: {lead.get('summary')}\n"
        f"Message ID: {lead.get('message_id')}\n"
        f"Time: {lead.get('processed_at')}"
    )


async def cooldown_active(r: redis.Redis, message_id: str) -> bool:
    return bool(await r.exists(f"{ALERT_COOLDOWN_PREFIX}{message_id}"))


async def set_cooldown(r: redis.Redis, message_id: str) -> None:
    await r.set(f"{ALERT_COOLDOWN_PREFIX}{message_id}", "1", ex=ALERT_COOLDOWN_SECONDS)


async def send_telegram(text: str) -> None:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": text})
        resp.raise_for_status()


async def send_lark(text: str) -> None:
    if not LARK_WEBHOOK_URL:
        return
    payload = {"msg_type": "text", "content": {"text": text}}
    async with httpx.AsyncClient(timeout=5.0) as client:
        resp = await client.post(LARK_WEBHOOK_URL, json=payload)
        resp.raise_for_status()


async def maybe_send_alert(r: redis.Redis, lead: dict[str, Any]) -> Optional[str]:
    if not ALERT_ENABLED:
        return None

    alert_type = evaluate_alert_type(lead)
    if not alert_type:
        return None

    if await cooldown_active(r, lead["message_id"]):
        logger.info("Alert cooldown active for %s", lead["message_id"])
        return None

    text = format_message(alert_type, lead)
    try:
        await send_telegram(text)
        await send_lark(text)
    except Exception as exc:
        # Demo UI reads alert_sent from Postgres — do not skip flag when Telegram/Lark fails.
        logger.error("Alert dispatch failed (recording alert in CRM anyway): %s", exc)

    await set_cooldown(r, lead["message_id"])
    ALERTS_SENT.labels(alert_type=alert_type).inc()
    return alert_type
