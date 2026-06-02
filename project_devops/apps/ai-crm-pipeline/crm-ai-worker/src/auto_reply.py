"""Agent 2 — Auto-reply BĐS: tự động phản hồi khách hàng bất động sản (tiếng Việt)."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Optional

from agents import AgentRole, get_agent
from config import CRM_SKIP_GEMINI
from metrics import LLM_LATENCY

logger = logging.getLogger(__name__)

_provider = None


def _get_provider():
    global _provider
    if _provider is None:
        _provider = get_agent(AgentRole.CRM_EXTRACT)
    return _provider


def should_auto_reply(extracted: dict[str, Any]) -> bool:
    """Quyết định có nên auto-reply cho lead BĐS không."""
    intent = extracted.get("intent", "other")
    urgency = extracted.get("urgency", "medium")
    sentiment = extracted.get("sentiment", "neutral")

    # Không auto-reply cho khách bức xúc + urgency cao — cần nhân viên xử lý
    if intent == "complaint" and urgency in ("high", "critical"):
        return False
    if sentiment == "negative" and urgency in ("high", "critical"):
        return False

    # Không auto-reply cho câu hỏi pháp lý phức tạp — cần chuyên viên pháp lý
    if intent == "legal_inquiry" and urgency in ("high", "critical"):
        return False

    # Auto-reply phù hợp cho: hỏi giá, đặt lịch xem, hỏi thông tin chung
    if intent in ("price_inquiry", "inquiry", "schedule_viewing") and urgency in ("low", "medium"):
        return True

    # Auto-reply cho khách mua/đầu tư urgency thấp-trung bình (warm lead)
    if intent in ("purchase", "other") and sentiment in ("positive", "neutral") and urgency in ("low", "medium"):
        return True

    return False


def _static_demo_reply(extracted: dict[str, Any], channel: str) -> str:
    """Fallback reply khi Gemini không khả dụng."""
    intent = extracted.get("intent", "inquiry")
    property_type = extracted.get("property_type", "bất động sản")
    location = extracted.get("location") or "khu vực bạn quan tâm"
    budget = extracted.get("budget_range")

    property_label = {
        "apartment": "căn hộ", "house": "nhà/biệt thự",
        "land": "đất nền", "commercial": "shophouse/mặt bằng",
    }.get(property_type, "bất động sản")

    if intent == "schedule_viewing":
        return (
            f"Xin chào! Cảm ơn bạn đã quan tâm đến {property_label} tại {location}. "
            f"Chuyên viên tư vấn của chúng tôi sẽ liên hệ xác nhận lịch xem nhà trong vòng 30 phút."
        )
    if intent == "price_inquiry":
        budget_note = f" trong tầm {budget}" if budget else ""
        return (
            f"Xin chào! Về giá {property_label} tại {location}{budget_note}, "
            f"chúng tôi có nhiều sản phẩm phù hợp. "
            f"Chuyên viên sẽ gửi bảng giá chi tiết và hỗ trợ bạn ngay."
        )
    if intent == "legal_inquiry":
        return (
            f"Xin chào! Về thông tin pháp lý của dự án, chúng tôi cam kết minh bạch 100%. "
            f"Chuyên viên tư vấn sẽ chuẩn bị hồ sơ pháp lý đầy đủ và liên hệ bạn sớm nhất."
        )
    # Default — general inquiry
    return (
        f"Xin chào! Cảm ơn bạn đã quan tâm. "
        f"Chúng tôi có nhiều {property_label} tại {location} phù hợp với nhu cầu của bạn. "
        f"Chuyên viên sẽ liên hệ tư vấn chi tiết trong thời gian sớm nhất."
    )


BDS_REPLY_SYSTEM = """Bạn là chuyên viên tư vấn bất động sản chuyên nghiệp của một công ty BĐS hàng đầu Việt Nam.
Nhiệm vụ: Soạn tin nhắn phản hồi khách hàng ngắn gọn, thân thiện, chuyên nghiệp bằng tiếng Việt.

Quy tắc bắt buộc:
- Tối đa 3 câu, không dài dòng
- KHÔNG hứa hẹn về ROI, lợi nhuận, hay tăng giá BĐS
- KHÔNG cam kết cụ thể về pháp lý, sổ đỏ, thời gian bàn giao
- Luôn kết thúc bằng đề xuất hành động cụ thể (xem nhà / gửi thông tin / tư vấn trực tiếp)
- Nếu khách hỏi giá: đề nghị được tư vấn trực tiếp để có báo giá chính xác
- Nếu khách muốn xem nhà: xác nhận sẽ liên hệ đặt lịch trong 30 phút
- Tông: Ấm áp, chuyên nghiệp, tạo sự tin tưởng
Output: plain text chỉ, không markdown, không JSON."""


def generate_reply(raw_text: str, extracted: dict[str, Any], channel: str) -> str:
    """Agent 2 — Generate CRM auto-reply for BĐS customer."""
    if CRM_SKIP_GEMINI:
        return _static_demo_reply(extracted, channel)

    llm = _get_provider()

    property_label = {
        "apartment": "căn hộ", "house": "nhà/biệt thự",
        "land": "đất nền", "commercial": "shophouse/mặt bằng",
    }.get(extracted.get("property_type", "other"), "bất động sản")

    prompt = (
        f"Khách hàng nhắn qua kênh {channel}:\n"
        f"\"{raw_text}\"\n\n"
        f"Thông tin phân tích:\n"
        f"- Loại BĐS: {property_label} | Vị trí: {extracted.get('location') or 'chưa xác định'}\n"
        f"- Mục đích: {extracted.get('transaction_type')} | Ngân sách: {extracted.get('budget_range') or 'chưa đề cập'}\n"
        f"- Ý định: {extracted.get('intent')} | Mức khẩn: {extracted.get('urgency')}\n\n"
        f"Soạn tin nhắn phản hồi phù hợp cho khách hàng này (tiếng Việt, tối đa 3 câu):"
    )

    messages = [
        {"role": "system", "content": BDS_REPLY_SYSTEM},
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
