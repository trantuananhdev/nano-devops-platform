"""T-19: Critic module — self-reflection on draft reports before final submission."""

import json
import logging
from typing import Any

from app.core.context_manager import truncate_text
from app.services.llm_router import AgentRole, llm_call
from app.services.orchestrator.types import CriticResult

logger = logging.getLogger(__name__)

CRITIC_SCHEMA_HINT = """{
    "approved": true | false,
    "issues": ["specific problems found in the draft"],
    "suggested_fixes": ["actionable fixes"]
}"""

_APPROVAL_PHRASES = (
    "đồng ý chủ trương",
    "phê duyệt theo đề xuất",
    "đồng ý phê duyệt",
)


def _normalize_risk(risk_level: Any) -> str:
    """Accept RiskLevel enum or plain string (e.g. 'high')."""
    if hasattr(risk_level, "value"):
        return str(risk_level.value)
    return str(risk_level)


def build_rule_based_verdict(
    report_md: str,
    checks: list[dict[str, Any]],
    risk_level: Any,
    *,
    resolution_md: str = "",
) -> CriticResult:
    """
    Rule-based critic for degraded mode and deterministic acceptance tests.

    Rejects when high-risk checks coexist with a low-risk approval draft
    (e.g. failed ERP checks but resolution says ĐỒNG Ý CHỦ TRƯƠNG).
    """
    risk = _normalize_risk(risk_level)
    issues: list[str] = []
    fixes: list[str] = []

    failed = [c for c in checks if c.get("status") == "fail"]
    resolution_lower = resolution_md.lower()
    report_lower = report_md.lower()

    approves = any(phrase in resolution_lower for phrase in _APPROVAL_PHRASES)
    requests_revision = "bổ sung" in resolution_lower or "đề nghị bổ sung" in resolution_lower

    if risk == "high" and approves and not requests_revision:
        issues.append("Mức rủi ro HIGH nhưng dự thảo Nghị quyết lại đề xuất phê duyệt")
        fixes.append("Sửa Nghị quyết thành ĐỀ NGHỊ BỔ SUNG HỒ SƠ trước khi phê duyệt")

    if failed and approves and not requests_revision:
        failed_labels = ", ".join(c.get("label", c.get("tool", "?")) for c in failed)
        issues.append(f"Có {len(failed)} kiểm tra FAIL ({failed_labels}) nhưng dự thảo lại phê duyệt")
        fixes.append("Phản ánh kết quả FAIL trong báo cáo và đề nghị bổ sung hồ sơ")

    for check in failed:
        label = check.get("label", check.get("tool", ""))
        if label and label.lower() not in report_lower and check.get("tool", "").lower() not in report_lower:
            issues.append(f"Báo cáo không đề cập kết quả FAIL: {label}")
            fixes.append(f"Bổ sung phân tích chi tiết cho {label}")

    if risk == "high" and "high" not in report_lower and "cao" not in report_lower:
        issues.append("Báo cáo không nhấn mạnh mức rủi ro cao")
        fixes.append("Thêm cảnh báo rủi ro cao ở phần tóm tắt")

    approved = len(issues) == 0
    return {
        "approved": approved,
        "issues": issues,
        "suggested_fixes": fixes,
        "source": "rules",
    }


async def review_draft(
    report_md: str,
    checks: list[dict[str, Any]],
    risk_level: Any,
    *,
    resolution_md: str = "",
    dossier_id: int | None = None,
) -> CriticResult:
    """Review draft report and resolution; LLM with rule-based fallback."""
    checks_summary = "\n".join(
        f"- {c.get('label', c.get('tool'))}: {c.get('status')} — {c.get('desc', '')}" for c in checks
    )
    risk = _normalize_risk(risk_level)

    messages = [
        {
            "role": "system",
            "content": (
                "You are an EVN Hanoi HDTV quality critic. "
                "Review the draft appraisal report and resolution for consistency with check results and risk level. "
                f"Respond ONLY with JSON:\n{CRITIC_SCHEMA_HINT}\n"
                "Set approved=false if risk is high but resolution approves, or if failed checks are ignored."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Risk level: {risk.upper()}\n\n"
                f"Checks:\n{checks_summary}\n\n"
                f"Report draft:\n{truncate_text(report_md, 750)}\n\n"
                f"Resolution draft:\n{truncate_text(resolution_md, 375)}"
            ),
        },
    ]

    try:
        raw = await llm_call(AgentRole.CRITIC, messages, response_format_json=True,
                             dossier_id=dossier_id)
        result = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(result, dict):
            raise TypeError("Critic response must be a JSON object")

        approved = bool(result.get("approved", True))
        issues = result.get("issues") or []
        fixes = result.get("suggested_fixes") or []
        if not isinstance(issues, list):
            issues = [str(issues)]
        if not isinstance(fixes, list):
            fixes = [str(fixes)]

        return {
            "approved": approved,
            "issues": issues,
            "suggested_fixes": fixes,
            "source": "llm",
        }
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Invalid critic JSON, using rule-based verdict: %s", exc)

    return build_rule_based_verdict(
        report_md, checks, risk_level, resolution_md=resolution_md
    )
