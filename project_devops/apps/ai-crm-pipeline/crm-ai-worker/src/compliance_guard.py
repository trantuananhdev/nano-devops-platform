"""Agent 6 — Compliance Guard: kiểm soát nội dung tư vấn BĐS theo pháp luật Việt Nam."""

from __future__ import annotations

import json
import logging
from typing import Any

from agents import AgentRole, get_agent
from config import CRM_SKIP_GEMINI

logger = logging.getLogger(__name__)

_ROI_WORDS = ("roi", "lợi nhuận", "sinh lời", "đảm bảo lãi", "tăng giá chắc")
_LEGAL_PROMISE = ("sổ đỏ chắc", "pháp lý sạch 100%", "cam kết pháp lý", "bàn giao đúng hạn chắc")


COMPLIANCE_SYSTEM = """Bạn là chuyên gia kiểm soát tuân thủ (Compliance Officer) cho một công ty Bất động sản Việt Nam.
Nhiệm vụ: Đánh giá nội dung tư vấn/phản hồi khách hàng để đảm bảo không vi phạm pháp luật và đạo đức kinh doanh.

Quy tắc KHÔNG ĐƯỢC phép (vi phạm = approved: false):
1. KHÔNG cam kết lợi nhuận đầu tư, ROI, tỷ lệ sinh lời cụ thể (ví dụ: "đảm bảo lãi 15%/năm")
2. KHÔNG hứa hẹn về mức tăng giá BĐS trong tương lai
3. KHÔNG tự ý xác nhận tình trạng pháp lý (sổ đỏ, giấy phép xây dựng) khi chưa kiểm tra hồ sơ
4. KHÔNG hứa hẹn thời hạn bàn giao cụ thể khi chưa có xác nhận từ chủ đầu tư
5. KHÔNG yêu cầu thông tin cá nhân nhạy cảm ngoài: họ tên, SĐT, thời gian xem nhà
6. KHÔNG chia sẻ thông tin cá nhân của khách hàng khác
7. Nếu khách tức giận/phàn nàn với urgency cao: phản hồi PHẢI de-escalate và mời gặp mặt trực tiếp
8. Tối đa 3 câu phản hồi, tiếng Việt, chuyên nghiệp

Trả về ONLY JSON hợp lệ theo schema:
{
  "approved": boolean,
  "rewritten_reply": string|null,
  "risk_flags": [string],
  "disclaimer": string|null
}
- approved: false nếu vi phạm bất kỳ quy tắc nào
- rewritten_reply: phiên bản đã sửa (nếu approved=false), null nếu approved=true
- risk_flags: danh sách mã vi phạm, ví dụ ["roi_guarantee", "legal_promise", "timeline_commit"]
- disclaimer: chuỗi cảnh báo thêm cho manager (nếu cần), null nếu không"""


def _safe_json_loads(text: str) -> dict[str, Any]:
    try:
        return json.loads(text)
    except Exception:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                return json.loads(text[start: end + 1])
            except Exception:
                pass
    return {}


def _rule_based_compliance(raw_text: str, draft_reply: str, extracted: dict[str, Any]) -> dict[str, Any]:
    combined = f"{raw_text} {draft_reply}".lower()
    risk_flags: list[str] = []
    if any(w in combined for w in _ROI_WORDS):
        risk_flags.append("roi_guarantee")
    if any(w in combined for w in _LEGAL_PROMISE):
        risk_flags.append("legal_promise")
    if extracted.get("intent") == "complaint" and extracted.get("urgency") in ("high", "critical"):
        risk_flags.append("escalate_complaint")
    disclaimer = None
    if risk_flags:
        disclaimer = "Cần review thủ công — tránh cam kết ROI/pháp lý."
    return {
        "approved": len(risk_flags) == 0,
        "rewritten_reply": None,
        "risk_flags": risk_flags,
        "disclaimer": disclaimer,
    }


def evaluate_reply(
    *,
    raw_text: str,
    draft_reply: str,
    extracted: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Returns compliance decision JSON (best-effort, never raises)."""
    extracted = extracted or {}
    if CRM_SKIP_GEMINI:
        return _rule_based_compliance(raw_text, draft_reply, extracted)

    llm = get_agent(AgentRole.COMPLIANCE_GUARD)

    context = {
        "raw_text": (raw_text or "")[:2000],
        "draft_reply": (draft_reply or "")[:2000],
        "intent": extracted.get("intent"),
        "urgency": extracted.get("urgency"),
        "sentiment": extracted.get("sentiment"),
        "property_type": extracted.get("property_type"),
        "location": extracted.get("location"),
        "transaction_type": extracted.get("transaction_type"),
        "budget_range": extracted.get("budget_range"),
    }
    messages = [
        {"role": "system", "content": COMPLIANCE_SYSTEM},
        {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
    ]

    try:
        out = llm.chat_text(messages=messages, json_mode=True)
        data = _safe_json_loads(out.strip())
        approved = bool(data.get("approved", True))
        rewritten = data.get("rewritten_reply")
        if rewritten:
            rewritten = str(rewritten).strip()[:2000]
        risk_flags = data.get("risk_flags") or []
        if not isinstance(risk_flags, list):
            risk_flags = [str(risk_flags)]
        disclaimer = data.get("disclaimer")
        if disclaimer:
            disclaimer = str(disclaimer).strip()[:1000]
        return {
            "approved": approved,
            "rewritten_reply": rewritten,
            "risk_flags": [str(x)[:120] for x in risk_flags][:8],
            "disclaimer": disclaimer,
        }
    except Exception as exc:
        logger.warning("Compliance guard failed, allow draft: %s", exc)
        return {
            "approved": True,
            "rewritten_reply": None,
            "risk_flags": ["guard_unavailable"],
            "disclaimer": None,
        }
