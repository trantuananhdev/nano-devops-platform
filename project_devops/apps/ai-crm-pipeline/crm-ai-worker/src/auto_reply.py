"""Gemini auto-reply for routine inquiries (Phase 4 demo)."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from geminiProvider import create_gemini_provider
from metrics import LLM_LATENCY

logger = logging.getLogger(__name__)

_provider = None


def _get_provider():
    global _provider
    if _provider is None:
        _provider = create_gemini_provider()
    return _provider


def should_auto_reply(extracted: dict[str, Any]) -> bool:
    intent = extracted.get("intent", "other")
    urgency = extracted.get("urgency", "medium")
    sentiment = extracted.get("sentiment", "neutral")

    if intent in ("cancel_order", "complaint") and urgency in ("high", "critical"):
        return False
    if sentiment == "negative" and urgency in ("high", "critical"):
        return False
    if intent in ("inquiry", "purchase") and urgency in ("low", "medium"):
        return True
    if intent == "other" and sentiment == "positive" and urgency in ("low", "medium"):
        return True
    return False


def _static_demo_reply(extracted: dict[str, Any], channel: str) -> str:
    intent = extracted.get("intent", "inquiry")
    product = extracted.get("product_interest") or "sản phẩm TNT"
    if intent == "purchase":
        return f"Cảm ơn bạn! Team TNT sẽ liên hệ về {product} trên {channel} trong vài phút."
    return (
        f"Xin chào! TNT Shop đã nhận tin của bạn trên {channel}. "
        f"Về {product}, bạn có thể xem giá trên shop hoặc đợi CS phản hồi thêm."
    )


def generate_reply(raw_text: str, extracted: dict[str, Any], channel: str) -> str:
    llm = _get_provider()
    prompt = (
        "You are TNT Shop CS bot. Reply in customer's language (tl/id/ms/en).\n"
        "Tone: friendly, short, max 2 sentences. Include product hint if inquiry.\n"
        f"Intent: {extracted.get('intent')}. Product: {extracted.get('product_interest')}\n"
        f"Channel: {channel}. Message: {raw_text}\n"
        "Output plain text only, no JSON."
    )
    messages = [
        {"role": "system", "content": "You are a helpful e-commerce customer service assistant."},
        {"role": "user", "content": prompt},
    ]
    try:
        start = time.perf_counter()
        text = llm.chat_text(messages=messages, json_mode=False)
        LLM_LATENCY.observe(time.perf_counter() - start)
        return (text or "").strip()[:2000]
    except Exception as exc:
        logger.warning("Auto-reply LLM failed, static fallback: %s", exc)
        return _static_demo_reply(extracted, channel)


def persist_auto_reply(conn, message_id: str, content: str) -> str:
    at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE leads
            SET auto_reply_sent = true,
                auto_reply_content = %s,
                auto_reply_at = %s::timestamptz
            WHERE message_id = %s
            """,
            (content, at, message_id),
        )
    conn.commit()
    return at
