"""Agent 3 — Trưởng phòng AI CRM: đánh giá lead và tạo brief vận hành cho quản lý BĐS."""

from __future__ import annotations

import logging
from typing import Any

from agents import AgentRole, get_agent
from config import CRM_SKIP_GEMINI

logger = logging.getLogger(__name__)

DEPT_HEAD_SYSTEM = """Bạn là Trưởng phòng AI của một công ty Bất động sản Việt Nam.
Nhiệm vụ: Dựa trên dữ liệu lead được cung cấp, tạo một brief vận hành ngắn gọn, quyết đoán bằng tiếng Việt cho quản lý kinh doanh.

Quy trình triage BĐS chuẩn:
1. Đánh giá mức độ ưu tiên (critical / high / medium / low) dựa trên urgency + intent + budget
2. Đề xuất hành động tiếp theo cụ thể (gọi ngay / đặt lịch xem nhà / gửi tài liệu pháp lý / theo dõi)
3. Nêu rủi ro nếu không hành động trong 24h
4. Gợi ý dự án/sản phẩm phù hợp dựa trên property_type + location + budget_range

Quy tắc bắt buộc:
- KHÔNG hứa hẹn về giá trị đầu tư, ROI, hay mức tăng giá trong tương lai
- KHÔNG cam kết về pháp lý, thời gian bàn giao, hay thủ tục sổ đỏ cụ thể
- Nếu khách hỏi về pháp lý phức tạp, yêu cầu chuyển cho luật sư chuyên nghiệp
- Nếu urgency = critical, hành động đầu tiên phải là "Gọi ngay trong 15 phút"

Output: 3-5 câu văn xuôi, không dùng bullet points, ngôn ngữ chuyên nghiệp BĐS."""


def _static_brief(lead_data: dict[str, Any]) -> str:
    urgency = lead_data.get("urgency", "medium")
    intent = lead_data.get("intent", "other")
    property_type = lead_data.get("property_type", "BĐS")
    location = lead_data.get("location", "chưa xác định")
    action_map = {
        "critical": "Gọi ngay trong 15 phút — khách có nhu cầu cực kỳ khẩn.",
        "high": "Liên hệ trong 1 giờ — khách đang tích cực tìm kiếm.",
        "medium": "Phân công CS follow up trong ngày.",
        "low": "Đưa vào nurture sequence, follow up trong 48h.",
    }
    action = action_map.get(urgency, "Theo dõi và phân loại thêm.")
    return (
        f"Lead {intent.upper()} — {property_type} tại {location}, ưu tiên {urgency.upper()}. "
        f"{action} "
        f"Tóm tắt: {lead_data.get('summary', 'Cần tư vấn thêm.')}"
    )


def generate_department_brief(lead_data: dict[str, Any]) -> str:
    """Generate AI manager brief for a BĐS lead (Agent 3)."""
    if CRM_SKIP_GEMINI:
        return _static_brief(lead_data)

    llm = get_agent(AgentRole.ODOO)

    # Build rich context for better brief generation
    budget_info = f"Ngân sách: {lead_data.get('budget_range')}" if lead_data.get("budget_range") else ""
    bedroom_info = f"Phòng ngủ: {lead_data.get('bedroom_count')}" if lead_data.get("bedroom_count") else ""
    transaction = lead_data.get("transaction_type", "other")
    transaction_label = {"buy": "Mua", "rent": "Thuê", "invest": "Đầu tư"}.get(transaction, "Chưa xác định")

    context = (
        f"Khách hàng: {lead_data.get('customer_name') or 'Ẩn danh'}\n"
        f"Điện thoại: {lead_data.get('phone') or 'Chưa có'}\n"
        f"Kênh: {lead_data.get('channel')} | Ngôn ngữ: {lead_data.get('language', 'Vietnamese')}\n"
        f"Loại BĐS: {lead_data.get('property_type')} | Vị trí: {lead_data.get('location')}\n"
        f"Mục đích: {transaction_label} | {budget_info} {bedroom_info}\n"
        f"Mức độ khẩn: {lead_data.get('urgency')} | Cảm xúc: {lead_data.get('sentiment')}\n"
        f"Ý định: {lead_data.get('intent')}\n"
        f"Tóm tắt nhu cầu: {lead_data.get('summary')}\n"
        f"Tin nhắn gốc: {(lead_data.get('raw_text') or '')[:400]}"
    )

    messages = [
        {"role": "system", "content": DEPT_HEAD_SYSTEM},
        {"role": "user", "content": context},
    ]
    try:
        return llm.chat_text(messages=messages).strip()[:4000]
    except Exception as exc:
        logger.warning("AI Dept Head brief generation failed: %s", exc)
        return _static_brief(lead_data)
