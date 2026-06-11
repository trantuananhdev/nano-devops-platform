"""T-23: Compose role-based system prompts and resolution drafts."""

from typing import Any

from app.models.entities import Dossier, RiskLevel, UserRole
from app.services.memory.retriever import build_preference_context
from app.services.orchestrator.prompts import ROLE_MODULES

_JSON_FORMAT_BLOCK = """
## Response Format
You MUST respond in JSON format with the following structure:
{
    "thought": "Your reasoning about what to do next",
    "action": "tool_call" or "finish",
    "tool_name": "Name of tool to call (only if action is tool_call)",
    "tool_input": {
        "dossier_id": 123,
        "doc_no": "123/TTr-B02",
        "title": "Dossier title",
        "query": "Specific query for this tool"
    }
}

## Decision Process
1. Assess the dossier and decide which tools are needed
2. Call tools sequentially in the legacy loop (plan orchestrator handles parallel batches)
3. After each tool, analyze the result
4. When you have enough information, finish and summarize

## Risk Assessment Rules
- High Risk: Budget exceeded OR inventory waste detected
- Medium Risk: Missing legal documents or unsigned docs
- Low Risk: All checks pass"""


def normalize_role(role: UserRole | str | None) -> UserRole:
    """Map unknown or missing roles to specialist (neutral default)."""
    if role is None:
        return UserRole.specialist
    if isinstance(role, UserRole):
        return role
    try:
        return UserRole(role)
    except ValueError:
        return UserRole.specialist


def _role_module(role: UserRole | str | None):
    return ROLE_MODULES[normalize_role(role).value]


def _tools_desc(tools: list[dict[str, Any]]) -> str:
    return "\n".join(
        f"- {t['name']}: {t['description']} (Category: {t['category']})"
        for t in tools
    )


def build_system_prompt(
    role: UserRole | str | None,
    tools: list[dict[str, Any]],
    preferences: dict[str, Any] | None = None,
) -> str:
    """Build ReAct system prompt for the given user role."""
    mod = _role_module(role)
    tools_desc = _tools_desc(tools)
    pref_section = build_preference_context(preferences or {})
    pref_block = f"\n\n{pref_section}" if pref_section else ""

    return (
        f"{mod.SYSTEM_PREAMBLE}\n\n"
        f"Available tools:\n{tools_desc}\n"
        f"{_JSON_FORMAT_BLOCK}{pref_block}\n\n"
        "Think carefully and act autonomously!"
    )


def build_planner_system(
    role: UserRole | str | None,
    tools: list[dict[str, Any]],
    *,
    pref_context: str = "",
    memory_context: str = "",
    feedback_lessons_context: str = "",
    plan_schema_hint: str,
) -> str:
    """Build planner-phase system prompt for the given user role."""
    mod = _role_module(role)
    tools_desc = "\n".join(
        f"- {t['name']}: {t['description']} (category: {t['category']})" for t in tools
    )
    pref_section = f"\n\nUser preferences:\n{pref_context}" if pref_context else ""
    mem_section = f"\n\nRelevant memories:\n{memory_context}" if memory_context else ""
    lessons_section = f"\n\n{feedback_lessons_context}" if feedback_lessons_context else ""

    return (
        f"{mod.PLANNER_PREAMBLE}\n\n"
        f"Available tools:\n{tools_desc}\n\n"
        f"Respond ONLY with JSON matching this schema:\n{plan_schema_hint}"
        f"{pref_section}{mem_section}{lessons_section}"
    )


def build_summary_system_prompt(role: UserRole | str | None) -> str:
    """Build LLM summary system instruction for report generation."""
    mod = _role_module(role)
    return mod.SUMMARY_INSTRUCTION


def build_resolution_md(
    role: UserRole | str | None,
    dossier: Dossier,
    overall_risk: RiskLevel,
    checks: list[dict[str, Any]],
) -> str:
    """Role-specific resolution draft — length and focus differ by profile."""
    mod = _role_module(role)
    risk_label = overall_risk.value.upper()
    failed = [c for c in checks if c.get("status") == "fail"]
    passed = [c for c in checks if c.get("status") == "pass"]

    if overall_risk == RiskLevel.high:
        decision = "ĐỀ NGHỊ BỔ SUNG HỒ SƠ trước khi phê duyệt."
    elif overall_risk == RiskLevel.medium:
        decision = "ĐỒNG Ý CHỦ TRƯƠNG có điều kiện — yêu cầu bổ sung căn cứ còn thiếu."
    else:
        decision = "ĐỒNG Ý CHỦ TRƯƠNG theo đề xuất."

    focus = mod.RESOLUTION_FOCUS

    if focus == "concise_risk_first":
        highlights = failed[:2] or passed[:1]
        bullet = "\n".join(f"- {c.get('label', c.get('tool', '?'))}: {c.get('status', '').upper()}" for c in highlights)
        return (
            f"# Dự thảo Nghị quyết (tóm tắt HĐTV)\n\n"
            f"**Rủi ro**: {risk_label}\n"
            f"**Quyết định**: {decision}\n\n"
            f"HĐTV ghi nhận Tờ trình {dossier.doc_no}.\n\n"
            f"## Điểm then chốt\n{bullet or '- Không có phát hiện bất thường.'}\n"
        )

    if focus == "checklist_supplements":
        lines = ["# Dự thảo Nghị quyết — Góc nhìn Trưởng ban\n"]
        lines.append(f"Tờ trình {dossier.doc_no} — {dossier.title}\n")
        lines.append(f"**Mức rủi ro đánh giá**: {risk_label}\n")
        lines.append("## Trạng thái checklist\n")
        for c in checks:
            status = c.get("status", "unknown").upper()
            lines.append(f"- [{status}] {c.get('label', c.get('tool', '?'))}: {c.get('desc', '')}")
        lines.append("\n## Đề xuất bổ sung hồ sơ\n")
        if failed:
            for c in failed:
                lines.append(f"- Bổ sung căn cứ cho: {c.get('label', c.get('tool', '?'))}")
        else:
            lines.append("- Không yêu cầu bổ sung — đủ điều kiện trình HĐTV.")
        lines.append(f"\n## Kết luận\n{decision}\n")
        return "\n".join(lines)

    if focus == "full_audit":
        lines = [
            "# Dự thảo Nghị quyết — Bản ghi kiểm toán đầy đủ\n",
            f"## Metadata\n- Số hiệu: {dossier.doc_no}\n- Đơn vị: {dossier.unit}\n- Rủi ro: {risk_label}\n",
            "## Audit trail — toàn bộ kiểm tra\n",
        ]
        for i, c in enumerate(checks, 1):
            lines.append(
                f"{i}. **{c.get('tool', '?')}** [{c.get('status', '').upper()}] "
                f"— {c.get('label', '')}: {c.get('desc', '')}"
            )
        lines.append(f"\n## Quyết định (không tóm tắt)\n{decision}\n")
        lines.append(
            f"Tổng số kiểm tra: {len(checks)} | Pass: {len(passed)} | Fail: {len(failed)}\n"
        )
        return "\n".join(lines)

    # full_technical (specialist default)
    lines = [
        "# Dự thảo Nghị quyết — Báo cáo kỹ thuật đầy đủ\n",
        f"## Hồ sơ\n- Số hiệu: {dossier.doc_no}\n- Tiêu đề: {dossier.title}\n"
        f"- Đơn vị trình: {dossier.unit}\n- Mức rủi ro: {risk_label}\n",
        "## Chi tiết kiểm tra\n",
    ]
    for c in checks:
        lines.append(
            f"### {c.get('label', c.get('tool', 'Check'))}\n"
            f"- Công cụ: {c.get('tool', 'N/A')}\n"
            f"- Kết quả: **{c.get('status', 'unknown').upper()}**\n"
            f"- Mô tả: {c.get('desc', 'Không có mô tả')}\n"
        )
    lines.append("## Phân tích rủi ro\n")
    if failed:
        lines.append("Các hạng mục không đạt:\n")
        for c in failed:
            lines.append(f"- {c.get('label')}: {c.get('desc')}")
    else:
        lines.append("Tất cả hạng mục kiểm tra đạt yêu cầu kỹ thuật.")
    lines.append(f"\n## Đề xuất\n{decision}\n")
    return "\n".join(lines)
