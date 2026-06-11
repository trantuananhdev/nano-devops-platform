"""T-17: LLM planning phase — produce structured execution plan JSON."""

import json
import logging
from typing import Any

from app.models.entities import Dossier, UserRole
from app.services.llm_router import AgentRole, llm_call
from app.services.orchestrator import prompt_builder
from app.services.orchestrator.types import ExecutionPlan

logger = logging.getLogger(__name__)

PLAN_SCHEMA_HINT = """{
    "goal": "Brief appraisal goal",
    "max_revisions": 2,
    "steps": [
        {
            "id": "step-1",
            "tool": "LegalGraphRAG",
            "parallel_group": null,
            "depends_on": [],
            "tool_input": {"query": "..."}
        },
        {
            "id": "step-2",
            "tool": "ErpBudgetCheck",
            "parallel_group": "financial",
            "depends_on": ["step-1"],
            "tool_input": {"query": "..."}
        },
        {
            "id": "step-3",
            "tool": "ErpInventoryCheck",
            "parallel_group": "financial",
            "depends_on": ["step-1"],
            "tool_input": {"query": "..."}
        }
    ]
}"""

_FINANCIAL_PARALLEL_TOOLS = frozenset({"ErpBudgetCheck", "ErpInventoryCheck"})


def build_fallback_plan(tools: list[dict[str, Any]], dossier: Dossier) -> ExecutionPlan:
    """Fallback plan with ERP financial tools grouped for parallel execution (T-18)."""
    base_input = {
        "dossier_id": dossier.id,
        "doc_no": dossier.doc_no,
        "title": dossier.title,
        "query": dossier.title,
    }
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

        steps.append({
            "id": step_id,
            "tool": t["name"],
            "parallel_group": parallel_group,
            "depends_on": deps,
            "tool_input": dict(base_input),
        })

    return {
        "goal": f"Appraise dossier {dossier.doc_no}",
        "max_revisions": 2,
        "steps": steps,
        "_fallback": True,
    }


def validate_plan(plan: dict[str, Any], tool_names: set[str]) -> bool:
    """Return True if plan has required structure and known tools."""
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
    """Ask LLM for an execution plan; fall back to sequential tool order on failure."""
    tool_names = {t["name"] for t in tools}
    obs_section = ""
    if prior_observations:
        obs_section = "\n\nPrior tool observations:\n" + "\n".join(prior_observations)

    system = prompt_builder.build_planner_system(
        role,
        tools,
        pref_context=pref_context,
        memory_context=memory_context,
        feedback_lessons_context=feedback_lessons_context,
        plan_schema_hint=PLAN_SCHEMA_HINT,
    )

    user_content = (
        f"Plan appraisal for dossier: {dossier.title} (Doc No: {dossier.doc_no}, unit: {dossier.unit})."
        f"{obs_section}"
    )
    if revision > 0:
        user_content += f"\nThis is revision #{revision} — add steps for any missing checks."

    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user_content},
    ]

    try:
        raw = await llm_call(AgentRole.PLANNER, messages, response_format_json=True)
        plan = json.loads(raw) if isinstance(raw, str) else raw
        if validate_plan(plan, tool_names):
            plan.setdefault("max_revisions", 2)
            plan.setdefault("goal", f"Appraise {dossier.doc_no}")
            return plan
        logger.warning("LLM plan failed validation, using fallback")
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Invalid plan JSON from LLM: %s", exc)

    return build_fallback_plan(tools, dossier)
