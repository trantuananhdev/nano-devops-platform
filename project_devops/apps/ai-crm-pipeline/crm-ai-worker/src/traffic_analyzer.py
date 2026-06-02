"""Agent 1 — Tổng hợp traffic sau demo burst (dùng khi gọi từ worker)."""

from __future__ import annotations

import json
import logging
from typing import Any

from agents import AgentRole, get_agent
from config import CRM_SKIP_GEMINI

logger = logging.getLogger(__name__)

TRAFFIC_SYSTEM = """Bạn là một nhà phân tích traffic CRM cho một bản demo công ty bất động sản Việt Nam.
Với một batch lead đã xử lý từ kịch bản traffic burst, viết một bản tóm tắt điều hành bằng tiếng Việt:
1) Tổng số lượng và tỷ lệ kênh
2) Số lượng lead nóng (urgency high/critical)
3) Ý định chính và xu hướng sentiment
4) Hành động đề xuất cho đội ngũ bán hàng hôm nay
Chỉ xuất JSON:
{"title_vi": string, "summary_vi": string, "hot_leads": number, "channels": object, "recommendations": [string]}"""


def _rule_based_summary(scenario_title: str, leads: list[dict[str, Any]]) -> dict[str, Any]:
    hot = sum(1 for L in leads if L.get("urgency") in ("high", "critical"))
    by_ch: dict[str, int] = {}
    for L in leads:
        ch = L.get("channel") or "unknown"
        by_ch[ch] = by_ch.get(ch, 0) + 1
    return {
        "title_vi": scenario_title,
        "summary_vi": f"Đã xử lý {len(leads)} lead, {hot} lead nóng (high/critical).",
        "hot_leads": hot,
        "channels": by_ch,
        "lead_count": len(leads),
        "recommendations": [
            "Ưu tiên gọi lead critical/high",
            "Theo dõi kênh có volume cao nhất",
        ],
    }


def analyze_traffic_batch(
    scenario_title: str,
    leads: list[dict[str, Any]],
) -> dict[str, Any]:
    if not leads:
        return {
            "title_vi": scenario_title or "Traffic burst",
            "summary_vi": "Chưa có lead nào được xử lý xong.",
            "hot_leads": 0,
            "channels": {},
            "recommendations": ["Chờ worker xử lý queue hoặc thử lại sau vài giây."],
            "lead_count": 0,
        }

    if not CRM_SKIP_GEMINI:
        compact = [
            {
                "channel": L.get("channel"),
                "urgency": L.get("urgency"),
                "intent": L.get("intent"),
                "sentiment": L.get("sentiment"),
                "summary": (L.get("summary") or "")[:120],
            }
            for L in leads[:50]
        ]
        llm = get_agent(AgentRole.TRAFFIC)
        messages = [
            {"role": "system", "content": TRAFFIC_SYSTEM},
            {
                "role": "user",
                "content": (
                    f"Scenario: {scenario_title}\nLeads ({len(leads)}):\n"
                    f"{json.dumps(compact, ensure_ascii=False)}"
                ),
            },
        ]
        try:
            raw = llm.chat_text(messages=messages, json_mode=True)
            parsed = json.loads(raw.strip())
            if isinstance(parsed, dict) and parsed.get("summary_vi"):
                parsed["lead_count"] = len(leads)
                return parsed
        except Exception as exc:
            logger.warning("Traffic analyst agent failed: %s", exc)

    return _rule_based_summary(scenario_title, leads)
