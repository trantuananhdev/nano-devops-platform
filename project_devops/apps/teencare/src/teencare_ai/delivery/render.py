from __future__ import annotations

from teencare_ai.core.types import ParentCopilotOutput
from teencare_ai.delivery.types import DeliveryAction, DeliveryPayload


def render_parent_payload(output: ParentCopilotOutput, *, channel: str = "push") -> DeliveryPayload:
    session_id = output["session_id"]
    risk_level = output.get("risk_level", "low")
    confidence = output.get("confidence", "low_signal")
    flag = output.get("flag", "")

    insights = output.get("insights", [])
    recs = output.get("recommendations", [])

    if flag == "insufficient_data":
        return {
            "session_id": session_id,
            "channel": channel,  # type: ignore[typeddict-item]
            "title": "Cần thêm dữ liệu để tạo insight tin cậy",
            "summary_bullets": [
                "Transcript buổi học quá ngắn/không rõ nên hệ thống không tạo insight để tránh sai lệch."
            ],
            "actions": [
                {
                    "label": "Nhờ mentor cập nhật ngắn",
                    "timing": "Hôm nay",
                    "details": "Yêu cầu mentor gửi 2–3 gạch đầu dòng về điểm chính và việc phụ huynh nên làm.",
                }
            ],
            "risk_level": risk_level,
            "confidence": confidence,
            "flag": flag,
        }

    title = "Tóm tắt buổi học & việc phụ huynh có thể làm"
    if risk_level == "high":
        title = "Cần lưu ý rủi ro cao — vui lòng xem kỹ"
    elif risk_level == "medium":
        title = "Có dấu hiệu căng thẳng — gợi ý 1–2 việc cụ thể"

    bullets: list[str] = []
    for ins in insights[:3]:
        obs = ins.get("observation", "").strip()
        if obs:
            bullets.append(obs)
    if not bullets:
        bullets = ["Chưa đủ tín hiệu rõ ràng để tóm tắt thành insight đáng tin cậy."]

    actions: list[DeliveryAction] = []
    for r in recs[:3]:
        action = (r.get("action") or "").strip()
        timing = (r.get("timing") or "").strip()
        outcome = (r.get("expected_outcome") or "").strip()
        if action and timing and outcome:
            actions.append({"label": action, "timing": timing, "details": outcome})

    return {
        "session_id": session_id,
        "channel": channel,  # type: ignore[typeddict-item]
        "title": title,
        "summary_bullets": bullets,
        "actions": actions,
        "risk_level": risk_level,
        "confidence": confidence,
        "flag": flag,
    }

