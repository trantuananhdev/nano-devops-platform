"""
Gemini Tool Simulator — giả lập phản hồi ERP/DOffice/PMIS/OCR qua Gemini Flash.

Tất cả tool calls được route qua llm_router._call_gemini với AgentRole.TOOL_MOCK
để audit log hiển thị đúng label "Gemini-Tool-Simulator" trên FE dashboard.
"""

import json
import logging
from typing import Any

from app.services.llm_router import AgentRole, _call_gemini

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Fallback responses (khi cả Gemini lẫn local LLM đều fail)
# ---------------------------------------------------------------------------
FALLBACK_RESPONSES: dict[str, dict[str, Any]] = {
    "ErpBudgetCheck": {
        "approved_budget_vnd": 50_000_000_000,
        "proposed_budget_vnd": 52_000_000_000,
        "variance_vnd":        2_000_000_000,
        "exceeded":            True,
        "note":                "Chi phí dự phòng vượt 2 tỷ so với ERP",
        "_source":             "fallback",
    },
    "ErpInventoryCheck": {
        "material_code":  "CVP-240",
        "stock_meters":   5000,
        "waste_warning":  True,
        "note":           "Cáp ngầm 240mm2 còn tồn kho",
        "_source":        "fallback",
    },
    "DOfficeLookup": {
        "doc_status":  "registered",
        "signed":      True,
        "attachments": 3,
        "_source":     "fallback",
    },
    "PmisProjectCheck": {
        "project_code": "DA-2026-BD",
        "phase":        "implementation",
        "on_schedule":  True,
        "_source":      "fallback",
    },
    "EcoOcrExtract": {
        "pages":    12,
        "summary":  "Tờ trình phê duyệt Kế hoạch đấu thầu Dự án Cáp ngầm Ba Đình",
        "_source":  "fallback",
    },
}


async def gemini_tool_response(
    tool_name:   str,
    params:      dict[str, Any],
    *,
    system_hint: str,
) -> dict[str, Any]:
    """Simulate a tool response using Gemini Flash (AgentRole.TOOL_MOCK).

    Falls back to FALLBACK_RESPONSES when Gemini is unavailable.
    The _source field indicates whether the result came from Gemini or fallback.
    """
    messages = [
        {
            "role": "system",
            "content": (
                f"{system_hint}\n"
                "Respond with valid JSON only, no markdown fences, no explanation.\n"
                f"Tool: {tool_name}"
            ),
        },
        {
            "role": "user",
            "content": f"Input parameters:\n{json.dumps(params, ensure_ascii=False)}",
        },
    ]

    try:
        raw = await _call_gemini(messages, temperature=0.2, json_mode=True)
        result = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(result, dict):
            result["_source"] = "gemini"
            result["_model"]  = AgentRole.TOOL_MOCK.value
            return result
        logger.warning("Gemini returned non-dict for tool %s — using fallback", tool_name)
    except Exception as exc:
        logger.warning("gemini_tool_response failed for %s: %s — using fallback", tool_name, exc)

    return {**FALLBACK_RESPONSES.get(tool_name, {"ok": True, "_source": "fallback"}), "params": params}
