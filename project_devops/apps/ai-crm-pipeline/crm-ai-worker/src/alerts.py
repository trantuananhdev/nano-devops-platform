"""Alert dispatch — BĐS-specific alert rules (hot lead, legal escalation, high budget)."""

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
    """
    Xác định loại cảnh báo BĐS.
    Priority order: critical_buyer > high_budget > legal_escalation > hot_lead > negative_sentiment
    """
    intent = lead.get("intent")
    urgency = lead.get("urgency")
    sentiment = lead.get("sentiment")
    budget_range = lead.get("budget_range")
    transaction_type = lead.get("transaction_type")

    # Critical buyer: muốn mua/xem gấp ngay hôm nay
    if urgency == "critical" and intent in ("purchase", "schedule_viewing"):
        return "critical_buyer"

    # High budget lead: có ngân sách cao và đang tìm kiếm tích cực
    if budget_range and urgency in ("high", "critical") and transaction_type in ("buy", "invest"):
        return "high_budget_lead"

    # Legal escalation: hỏi pháp lý phức tạp với urgency cao — cần chuyên viên pháp lý
    if intent == "legal_inquiry" and urgency in ("high", "critical"):
        return "legal_escalation"

    # Hot lead chung: urgency cao, bất kể intent
    if urgency in ("high", "critical"):
        return "hot_lead"

    # Negative sentiment cần can thiệp sớm
    if sentiment == "negative":
        return "negative_sentiment"

    return None


def _format_property_line(lead: dict[str, Any]) -> str:
    parts = []
    if lead.get("property_type"):
        labels = {"apartment": "Căn hộ", "house": "Nhà/Biệt thự", "land": "Đất nền", "commercial": "Shophouse/TMDV"}
        parts.append(labels.get(lead["property_type"], lead["property_type"]))
    if lead.get("location"):
        parts.append(f"tại {lead['location']}")
    if lead.get("budget_range"):
        parts.append(f"— Ngân sách: {lead['budget_range']}")
    if lead.get("bedroom_count"):
        parts.append(f"({lead['bedroom_count']})")
    return " ".join(parts) if parts else "Chưa xác định"


def format_message(alert_type: str, lead: dict[str, Any]) -> str:
    alert_labels = {
        "critical_buyer": "🔴 CRITICAL BUYER — Khách muốn mua/xem GẤP",
        "high_budget_lead": "💰 HIGH BUDGET — Khách ngân sách cao",
        "legal_escalation": "⚖️ PHÁP LÝ — Cần chuyên viên pháp lý",
        "hot_lead": "🔥 HOT LEAD — Ưu tiên cao",
        "negative_sentiment": "⚠️ NEGATIVE — Cần can thiệp ngay",
    }
    label = alert_labels.get(alert_type, f"🚨 CRM Alert — {alert_type}")

    transaction_label = {
        "buy": "Mua", "rent": "Thuê", "invest": "Đầu tư",
    }.get(lead.get("transaction_type", ""), "")

    intent_label = {
        "purchase": "Mua BĐS", "schedule_viewing": "Đặt lịch xem nhà",
        "price_inquiry": "Hỏi giá", "legal_inquiry": "Hỏi pháp lý",
        "inquiry": "Tư vấn chung", "complaint": "Phàn nàn", "other": "Khác",
    }.get(lead.get("intent", ""), lead.get("intent", ""))

    return (
        f"{label}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 Khách: {lead.get('customer_name') or 'Ẩn danh'} | 📱 {lead.get('phone') or 'Chưa có SĐT'}\n"
        f"📢 Kênh: {lead.get('channel')} | 🎯 Ý định: {intent_label}{' | ' + transaction_label if transaction_label else ''}\n"
        f"🏠 BĐS: {_format_property_line(lead)}\n"
        f"📊 Urgency: {lead.get('urgency')} | Cảm xúc: {lead.get('sentiment')}\n"
        f"📝 Tóm tắt: {lead.get('summary') or lead.get('raw_text', '')[:200]}\n"
        f"🆔 Message ID: {lead.get('message_id')}\n"
        f"⏰ {lead.get('processed_at')}"
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
