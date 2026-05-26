"""CRM extraction — uses geminiProvider (same contract as ai-agent)."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from geminiProvider import create_gemini_provider
from config import CRM_DEMO_LLM_FALLBACK
from metrics import LLM_LATENCY

logger = logging.getLogger(__name__)

URGENCY = frozenset({"low", "medium", "high", "critical"})
SENTIMENT = frozenset({"positive", "neutral", "negative"})
INTENT = frozenset({"purchase", "inquiry", "cancel_order", "complaint", "other"})

SYSTEM_INSTRUCTION = """You are a CRM data extraction engine for Southeast Asian e-commerce.
Input message may be Tagalog, Indonesian, English, or mixed slang.
Extract structured fields. Output ONLY valid JSON matching this schema:
{"customer_name": string|null, "phone": string|null, "product_interest": string|null,
"urgency": "low"|"medium"|"high"|"critical",
"sentiment": "positive"|"neutral"|"negative",
"intent": "purchase"|"inquiry"|"cancel_order"|"complaint"|"other",
"language": string|null, "summary": string}
Rules:
- urgency=critical if cancel/refund/chargeback anger or legal threat
- intent=cancel_order if user wants to cancel
- sentiment=negative if insults or strong dissatisfaction"""

_provider = None


def _get_provider():
    global _provider
    if _provider is None:
        _provider = create_gemini_provider()
    return _provider


def _coerce_enum(value: str | None, allowed: frozenset[str], default: str) -> str:
    if value and value.lower() in allowed:
        return value.lower()
    if value:
        logger.warning("Invalid enum value %s, using %s", value, default)
    return default


def normalize_extraction(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "customer_name": data.get("customer_name"),
        "phone": data.get("phone"),
        "product_interest": data.get("product_interest"),
        "urgency": _coerce_enum(data.get("urgency"), URGENCY, "medium"),
        "sentiment": _coerce_enum(data.get("sentiment"), SENTIMENT, "neutral"),
        "intent": _coerce_enum(data.get("intent"), INTENT, "other"),
        "language": data.get("language"),
        "summary": data.get("summary") or "",
    }


def demo_fallback_extract(
    raw_text: str,
    channel: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Rule-based extraction when Gemini is unavailable (demo continuity)."""
    payload = payload or {}
    text = raw_text.lower()
    category = (payload.get("demo_category") or "").lower()

    intent = category if category in INTENT else "other"
    if intent == "other":
        if any(w in text for w in ("cancel", "chargeback", "refund", "hủy", "huỷ")):
            intent = "cancel_order"
        elif any(w in text for w in ("complaint", "wrong item", "salah", "rosak", "defect")):
            intent = "complaint"
        elif any(w in text for w in ("price", "harga", "presyo", "cod", "tracking", "voucher")):
            intent = "inquiry"
        elif any(w in text for w in ("buy", "order", "mua", "beli")):
            intent = "purchase"

    urgency = "medium"
    if intent in ("cancel_order", "complaint") and any(
        w in text for w in ("chargeback", "lawyer", "24 hour", "refund now", "sue")
    ):
        urgency = "critical"
    elif intent in ("cancel_order", "complaint"):
        urgency = "high"
    elif intent == "inquiry":
        urgency = "low"

    sentiment = "neutral"
    if any(w in text for w in ("angry", "terrible", "scam", "worst", "galit", "marah")):
        sentiment = "negative"
    elif any(w in text for w in ("thank", "love", "great", "salamat", "terima kasih")):
        sentiment = "positive"

    locale = payload.get("locale") or ""
    language = "English"
    if locale.startswith("tl") or "tagalog" in text:
        language = "Tagalog"
    elif locale.startswith("id") or "harga" in text or "pesan" in text:
        language = "Indonesian"
    elif locale.startswith("ms") or "boleh" in text or "cod" in text:
        language = "Malay"

    return normalize_extraction(
        {
            "customer_name": payload.get("customer_name"),
            "phone": payload.get("phone"),
            "product_interest": payload.get("product_interest"),
            "urgency": urgency,
            "sentiment": sentiment,
            "intent": intent,
            "language": language,
            "summary": f"[Demo fallback] {intent} on {channel} — LLM rate-limited, rule-based triage.",
        }
    )


def extract_fields(
    raw_text: str,
    channel: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    llm = _get_provider()
    messages = [
        {"role": "system", "content": SYSTEM_INSTRUCTION},
        {"role": "user", "content": f"Message: {raw_text}\nChannel: {channel}"},
    ]

    try:
        start = time.perf_counter()
        text = llm.chat_text(messages=messages, json_mode=True)
        LLM_LATENCY.observe(time.perf_counter() - start)

        text = text.strip()
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                raise
            parsed = json.loads(match.group())
        return normalize_extraction(parsed)
    except Exception as exc:
        if CRM_DEMO_LLM_FALLBACK:
            logger.warning("LLM extract failed, using demo fallback: %s", exc)
            return demo_fallback_extract(raw_text, channel, payload)
        raise
