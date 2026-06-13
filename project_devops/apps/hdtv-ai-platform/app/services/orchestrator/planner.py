"""T-17: LLM planning phase — produce structured execution plan JSON.

Planning improvements:
- Injects rich dossier context (pdf_excerpt, risk_level, unit) into user message
- Accepts pre-formatted memory_context string (supports build_memory_context)
- Passes cross-dossier similar patterns when available
- Falls back gracefully to rule-based plan
"""

import json
import logging
from typing import Any

from app.models.entities import Dossier, UserRole
from app.services.llm_router import AgentRole, llm_call
from app.services.orchestrator import prompt_builder
from app.services.orchestrator.types import ExecutionPlan

logger = logging.getLogger(__name__)

PLAN_SCHEMA_HINT = """{
    "goal": "Brief appraisal goal in Vietnamese",
    "max_revisions": 2,
    "steps": [
        {
            "id": "step-1",
            "tool": "LegalGraphRAG",
            "parallel_group": null,
            "depends_on": [],
            "tool_input": {"query": "căn cứ pháp lý hồ sơ mua sắm UAV"}
        },
        {
            "id": "step-2",
            "tool": "ErpBudgetCheck",
            "parallel_group": "financial",
            "depends_on": ["step-1"],
            "tool_input": {"query": "ngân sách mua sắm thiết bị UAV 4 bộ"}
        },
        {
            "id": "step-3",
            "tool": "ErpInventoryCheck",
            "parallel_group": "financial",
            "depends_on": ["step-1"],
            "tool_input": {"query": "tồn kho thiết bị bay"}
        }
    ]
}"""

_FINANCIAL_PARALLEL_TOOLS = frozenset({"ErpBudgetCheck", "ErpInventoryCheck"})

# Max chars of pdf_text to inject into planner (keep context concise)
_PDF_CONTEXT_MAX_CHARS = 800


def _build_dossier_context(dossier: Dossier) -> str:
    """Build a rich context block about the dossier for the planner.

    Includes:
    - Basic identifiers (doc_no, title, unit)
    - Current risk level if already known
    - Key excerpt from PDF text (first _PDF_CONTEXT_MAX_CHARS chars)
    """
    lines = [
        "## Dossier to appraise",
        f"- Doc No: {dossier.doc_no}",
        f"- Title: {dossier.title}",
        f"- Unit: {getattr(dossier, 'unit', 'N/A') or 'N/A'}",
    ]

    risk = getattr(dossier, "risk_level", None)
    if risk:
        risk_val = risk.value if hasattr(risk, "value") else str(risk)
        lines.append(f"- Current risk level: {risk_val} (may change after appraisal)")

    pdf_text = getattr(dossier, "pdf_text", None) or ""
    if pdf_text:
        excerpt = pdf_text[:_PDF_CONTEXT_MAX_CHARS].strip()
        if len(pdf_text) > _PDF_CONTEXT_MAX_CHARS:
            excerpt += "… [truncated]"
        lines.append("\n## Document excerpt (from uploaded PDF)")
        lines.append(excerpt)

    return "\n".join(lines)


def build_fallback_plan(tools: list[dict[str, Any]], dossier: Dossier) -> ExecutionPlan:
    """Fallback plan: sequential execution, ERP financial tools in parallel (T-18)."""
    base_input = {
        "dossier_id": dossier.id,
        "doc_no": dossier.doc_no,
        "title": dossier.title,
        "query": dossier.title,
        "unit": getattr(dossier, "unit", "") or "",
    }

    pdf_text = getattr(dossier, "pdf_text", None) or ""
    if pdf_text:
        base_input["pdf_excerpt"] = pdf_text[:600].strip()

    steps: list[dict[str, Any]] = []
    last_non_financial_id: str | None = None

    for i, t in enumerate(tools):
        step_id = f"step-{i + 1}"
        is_financial = t["name"] in _FINANCIAL_PARALLEL_TOOLS

        if is_financial:
            deps = [last_non_financial_id] if last_non_financial_id else (
                [steps[-1]["id"]] if steps else []
            )
            parallel_group = "financial"
        else:
            deps = [steps[-1]["id"]] if steps else []
            parallel_group = None
            last_non_financial_id = step_id

        # Build a more specific query from dossier content
        specific_query = _build_tool_query(t["name"], dossier)

        steps.append({
            "id": step_id,
            "tool": t["name"],
            "parallel_group": parallel_group,
            "depends_on": deps,
            "tool_input": {**base_input, "query": specific_query},
        })

    return {
        "goal": f"Thẩm định hồ sơ {dossier.doc_no} — {dossier.title}",
        "max_revisions": 2,
        "steps": steps,
        "_fallback": True,
    }


def _build_tool_query(tool_name: str, dossier: Dossier) -> str:
    """Build a specific query string for a tool based on dossier content."""
    title = dossier.title or ""
    doc_no = dossier.doc_no or ""
    unit = getattr(dossier, "unit", "") or ""

    queries = {
        "LegalGraphRAG": f"căn cứ pháp lý thẩm quyền phê duyệt {doc_no} — {title}",
        "ErpBudgetCheck": f"kiểm tra ngân sách đầu tư mua sắm {title}",
        "ErpInventoryCheck": f"tồn kho vật tư thiết bị liên quan {title}",
        "TechnicalStandardCheck": f"tiêu chuẩn kỹ thuật {title}",
        "ProcurementCheck": f"quy trình mua sắm đấu thầu {doc_no}",
        "DOfficeLookup": f"đăng ký hồ sơ văn phòng {doc_no} {unit}",
        "PmisProjectCheck": f"tiến độ dự án {doc_no} {unit}",
        "EcoOcrExtract": f"trích xuất nội dung hồ sơ PDF {doc_no}",
    }
    return queries.get(tool_name, title)


def validate_plan(plan: dict[str, Any], tool_names: set[str]) -> bool:
    """Return True if plan has required structure and only uses known tools."""
    if not isinstance(plan, dict):
        return False
    steps = plan.get("steps")
    if not isinstance(steps, list) or len(steps) == 0:
        return False
    for step in steps:
        if not isinstance(step, dict):
            return False
        if not step.get("id") or not step.get("tool"):
            return False
        if step["tool"] not in tool_names:
            return False
    return True


async def create_plan(
    dossier: Dossier,
    tools: list[dict[str, Any]],
    *,
    role: UserRole | str | None = None,
    pref_context: str = "",
    memory_context: str = "",
    feedback_lessons_context: str = "",
    revision: int = 0,
    prior_observations: list[str] | None = None,
) -> ExecutionPlan:
    """Ask LLM for an execution plan; fall back to rule-based plan on failure.

    Context injected into the planner:
    1. System prompt: role-specific instructions + tool list + memory + lessons
    2. User message: rich dossier context (doc_no, title, unit, risk, pdf_excerpt)
    3. Prior observations (for revision): what was found in the previous pass
    """
    tool_names = {t["name"] for t in tools}

    # Rich dossier context block
    dossier_ctx = _build_dossier_context(dossier)

    # Prior observations section
    obs_section = ""
    if prior_observations:
        obs_section = (
            "\n\n## Prior tool observations (from previous execution pass)\n"
            + "\n".join(f"- {o}" for o in prior_observations[-5:])  # last 5 only
        )

    system = prompt_builder.build_planner_system(
        role,
        tools,
        pref_context=pref_context,
        memory_context=memory_context,
        feedback_lessons_context=feedback_lessons_context,
        plan_schema_hint=PLAN_SCHEMA_HINT,
    )

    user_content = (
        f"{dossier_ctx}"
        f"{obs_section}"
        f"\n\nProduce an execution plan as JSON matching the schema above."
    )
    if revision > 0:
        user_content += (
            f"\n\nIMPORTANT: This is revision #{revision}. "
            "Add steps only for checks that failed or were not covered. "
            "Do NOT repeat checks that already passed."
        )

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]

    try:
        raw = await llm_call(AgentRole.PLANNER, messages, response_format_json=True,
                             dossier_id=dossier.id)
        plan = json.loads(raw) if isinstance(raw, str) else raw
        if validate_plan(plan, tool_names):
            plan.setdefault("max_revisions", 2)
            plan.setdefault("goal", f"Thẩm định {dossier.doc_no} — {dossier.title}")
            return plan
        logger.warning("LLM plan failed validation (unknown tools or bad structure), using fallback")
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Invalid plan JSON from LLM: %s", exc)
    except Exception as exc:
        logger.warning("LLM plan call failed: %s", exc)

    return build_fallback_plan(tools, dossier)
