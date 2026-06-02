"""CRM extraction engine — Gemini-powered BĐS lead intelligence (Agent 2)."""

from __future__ import annotations

import json
import logging
import re
import time
from typing import Any

from agents import AgentRole, get_agent
from config import CRM_DEMO_LLM_FALLBACK, CRM_SKIP_GEMINI
from metrics import LLM_LATENCY

logger = logging.getLogger(__name__)

# --- Enum value sets ---
URGENCY = frozenset({"low", "medium", "high", "critical"})
SENTIMENT = frozenset({"positive", "neutral", "negative"})
INTENT = frozenset({
    "purchase", "inquiry", "schedule_viewing",
    "price_inquiry", "legal_inquiry", "complaint", "other",
})
PROPERTY_TYPES = frozenset({"apartment", "house", "land", "commercial", "other"})
TRANSACTION_TYPES = frozenset({"buy", "rent", "invest", "other"})

SYSTEM_INSTRUCTION = """Bạn là một hệ thống trích xuất dữ liệu CRM cao cấp cho một công ty bất động sản Việt Nam.
Tin nhắn đầu vào có thể là tiếng Việt, tiếng Anh, hoặc tiếng mixed (slang BĐS, nhà đất).
Trích xuất các trường có cấu trúc. CHỈ xuất ra JSON hợp lệ theo schema này:
{
  "customer_name": string|null,
  "phone": string|null,
  "property_type": "apartment"|"house"|"land"|"commercial"|"other",
  "location": string|null,
  "transaction_type": "buy"|"rent"|"invest"|"other",
  "budget_range": string|null,
  "bedroom_count": string|null,
  "urgency": "low"|"medium"|"high"|"critical",
  "sentiment": "positive"|"neutral"|"negative",
  "intent": "purchase"|"inquiry"|"schedule_viewing"|"price_inquiry"|"legal_inquiry"|"complaint"|"other",
  "language": string|null,
  "summary": string
}
Quy tắc trích xuất (chính xác):
- property_type: "apartment" nếu là căn hộ/chung cư/penthouse/studio, "house" nếu là nhà/biệt thự/townhouse, "land" nếu là đất/dất nền/dất thổ cư, "commercial" nếu là shophouse/văn phòng/mặt bằng/mặt tiền
- transaction_type: "buy" nếu mua/đặt cọc/sở hữu, "rent" nếu thuê/cho thuê, "invest" nếu đầu tư/sinh lời/ROI, còn lại "other"
- budget_range: trích xuất các đề cập ngân sách như "2-3 tỷ", "dưới 5 tỷ", "10 triệu/tháng" như một string; null nếu không đề cập
- bedroom_count: trích xuất "2PN", "3 phòng ngủ", "studio" như cũ; null nếu không đề cập
- urgency: "critical" nếu muốn xem ngay hôm nay/đặt cọc gấp/cần ngay; "high" nếu muốn xem sớm/đang tìm kiếm tích cực; "medium" cho hỏi thông tin chung; "low" cho duyệt nhẹ nhàng
- intent: "schedule_viewing" nếu muốn đặt lịch xem nhà; "price_inquiry" nếu hỏi cụ thể về giá; "legal_inquiry" nếu hỏi về sổ đỏ/pháp lý/giấy phép; "purchase" nếu thể hiện ý định mua; "complaint" nếu có trải nghiệm tiêu cực; "inquiry" cho thông tin chung
- sentiment: "negative" cho phàn nàn/bực xúc/tức giận; "positive" cho hào hứng/vui vẻ/thích; còn lại "neutral"
- summary: tóm tắt ngắn gọn 1-2 câu tiếng Việt về nhu cầu khách hàng và loại BĐS quan tâm
- location: trích xuất thành phố/quận/khu vực (ví dụ: "Quận 1", "Bình Thạnh", "TP.HCM", "Hà Nội")"""

_provider = None


def _get_provider():
    global _provider
    if _provider is None:
        _provider = get_agent(AgentRole.CRM_EXTRACT)
    return _provider


def extract_from_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Use pre-analyzed fields from Telegram agent 5 (skip Gemini extract)."""
    return normalize_extraction(
        {
            "customer_name": payload.get("customer_name"),
            "phone": payload.get("phone"),
            "property_type": payload.get("property_type"),
            "location": payload.get("location"),
            "transaction_type": payload.get("transaction_type", "other"),
            "budget_range": payload.get("budget_range"),
            "bedroom_count": payload.get("bedroom_count"),
            "urgency": payload.get("urgency", "medium"),
            "sentiment": payload.get("sentiment", "neutral"),
            "intent": payload.get("intent", "other"),
            "language": payload.get("language"),
            "summary": payload.get("summary") or "",
        }
    )


def _coerce_enum(value: str | None, allowed: frozenset[str], default: str) -> str:
    if value and value.lower() in allowed:
        return value.lower()
    if value:
        logger.warning("Invalid enum value %r, using default=%r", value, default)
    return default


def normalize_extraction(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "customer_name": data.get("customer_name"),
        "phone": data.get("phone"),
        "property_type": _coerce_enum(data.get("property_type"), PROPERTY_TYPES, "other"),
        "location": data.get("location"),
        "transaction_type": _coerce_enum(data.get("transaction_type"), TRANSACTION_TYPES, "other"),
        "budget_range": data.get("budget_range"),
        "bedroom_count": data.get("bedroom_count"),
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
    """Rule-based BDS extraction when Gemini is unavailable (demo continuity)."""
    payload = payload or {}
    text = raw_text.lower()
    category = (payload.get("demo_category") or "").lower()

    # --- Intent detection (BDS-specific priority order) ---
    intent = category if category in INTENT else "other"
    if intent == "other":
        if any(w in text for w in ("xem nha", "lich xem", "dat lich", "cho xem", "tham quan", "viewing schedule")):
            intent = "schedule_viewing"
        elif any(w in text for w in ("so do", "phap ly", "giay phep", "quy hoach", "hop dong phap", "legal", "thu tuc")):
            intent = "legal_inquiry"
        elif any(w in text for w in ("gia bao nhieu", "gia ca", "bao nhieu tien", "phi", "price", "cost", "bao nhieu")):
            intent = "price_inquiry"
        elif any(w in text for w in ("mua", "dat coc", "ky hop dong", "purchase", "buy", "so huu")):
            intent = "purchase"
        elif any(w in text for w in ("phan nan", "complaint", "buc xuc", "tuc", "khong hai long", "kem chat luong")):
            intent = "complaint"
        elif any(w in text for w in ("hoi", "thong tin", "inquiry", "tu van", "cho biet", "muon biet")):
            intent = "inquiry"

    # --- Property type ---
    property_type = payload.get("property_type") or "other"
    text_raw = raw_text.lower()
    if any(w in text_raw for w in ("can ho", "chung cu", "apartment", "penthouse", "studio")):
        property_type = "apartment"
    elif any(w in text_raw for w in ("biet thu", "nha pho", "nha rieng", "villa", "townhouse")):
        property_type = "house"
    elif any(w in text_raw for w in ("dat nen", "dat du an", "dat tho cu", "dat", "land")):
        property_type = "land"
    elif any(w in text_raw for w in ("shophouse", "van phong", "mat bang", "commercial", "mat tien")):
        property_type = "commercial"

    # --- Transaction type ---
    transaction_type = "other"
    if any(w in text_raw for w in ("dau tu", "sinh loi", "loi nhuan", "roi", "invest", "tang gia")):
        transaction_type = "invest"
    elif any(w in text_raw for w in ("thue", "cho thue", "rent", "tien thue")):
        transaction_type = "rent"
    elif any(w in text_raw for w in ("mua", "so huu", "dat coc", "buy", "purchase")):
        transaction_type = "buy"

    # --- Urgency ---
    urgency = "medium"
    if any(w in text_raw for w in ("ngay hom nay", "gap", "urgent", "khan", "ngay bay gio", "hom nay")):
        urgency = "critical"
    elif intent in ("schedule_viewing", "purchase") and any(
        w in text_raw for w in ("som", "tuan nay", "nhanh", "this week")
    ):
        urgency = "high"
    elif intent in ("price_inquiry", "legal_inquiry", "purchase"):
        urgency = "high"
    elif intent in ("inquiry", "other"):
        urgency = "low"

    # --- Sentiment ---
    sentiment = "neutral"
    if any(w in text_raw for w in ("te", "buc xuc", "tuc", "kien", "scam", "lua", "khong hai long")):
        sentiment = "negative"
    elif any(w in text_raw for w in ("cam on", "tuyet", "tot qua", "thich", "hai long", "great", "love")):
        sentiment = "positive"

    locale = payload.get("locale") or ""
    language = "Vietnamese"
    if locale.startswith("en") or ("hello" in text_raw and "xin chao" not in text_raw):
        language = "English"

    # --- Budget extraction (simple regex pattern) ---
    budget_range: str | None = None
    budget_m = re.search(
        r"([\d,.]+\s*(?:ty|tỷ|trieu|triệu|tr|million|billion)[^,.]{0,20})",
        raw_text, re.IGNORECASE,
    )
    if budget_m:
        budget_range = budget_m.group(1).strip()[:60]

    # --- Bedroom count ---
    bedroom_count: str | None = None
    br_m = re.search(r"(\d+)\s*(?:pn|phong ngu|phòng ngủ|bedroom|br)\b", raw_text, re.IGNORECASE)
    if br_m:
        bedroom_count = f"{br_m.group(1)}PN"

    location = payload.get("location")
    summary = (
        f"Khách {transaction_type.upper()} {property_type} tại {location or channel}."
        f" Nhu cầu: {intent}."
    )

    return normalize_extraction(
        {
            "customer_name": payload.get("customer_name"),
            "phone": payload.get("phone"),
            "property_type": property_type,
            "location": location,
            "transaction_type": transaction_type,
            "budget_range": budget_range,
            "bedroom_count": bedroom_count,
            "urgency": urgency,
            "sentiment": sentiment,
            "intent": intent,
            "language": language,
            "summary": summary,
        }
    )


def extract_fields(
    raw_text: str,
    channel: str,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if CRM_SKIP_GEMINI:
        return demo_fallback_extract(raw_text, channel, payload)

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
