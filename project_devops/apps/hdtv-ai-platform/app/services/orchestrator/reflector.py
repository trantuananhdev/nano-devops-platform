"""T-17: Reflection phase — decide if plan results are sufficient or need revision."""

import json
import logging
from typing import Any

from app.models.entities import Dossier
from app.services.llm_router import AgentRole, llm_call
from app.services.orchestrator.planner import validate_plan
from app.services.orchestrator.types import ReflectionResult, ReflectionVerdict

logger = logging.getLogger(__name__)

REFLECT_SCHEMA_HINT = """{
    "verdict": "sufficient" | "revise" | "escalate",
    "reason": "Brief explanation",
    "revised_steps": [
        {
            "id": "step-rev-1",
            "tool": "ToolName",
            "parallel_group": null,
            "depends_on": [],
            "tool_input": {}
        }
    ]
}"""


def build_fallback_reflection(
    checks: list[dict[str, Any]],
    plan: dict[str, Any],
    tools: list[dict[str, Any]],
    dossier: Dossier,
) -> ReflectionResult:
    """Rule-based reflection when LLM is unavailable."""
    failed = [c for c in checks if c.get("status") == "fail"]
    executed_tools = {c.get("tool") for c in checks}
    planned_tools = {s.get("tool") for s in plan.get("steps", [])}
    missing_tools = planned_tools - executed_tools

    if failed:
        revised = []
        for i, check in enumerate(failed):
            tool = check.get("tool")
            if tool:
                revised.append(
                    {
                        "id": f"rev-{i + 1}",
                        "tool": tool,
                        "parallel_group": None,
                        "depends_on": [],
                        "tool_input": {
                            "dossier_id": dossier.id,
                            "doc_no": dossier.doc_no,
                            "title": dossier.title,
                            "query": f"Re-check after failure: {check.get('label', '')}",
                        },
                    }
                )
        if revised:
            return {"verdict": "revise", "reason": "Failed checks require re-execution", "revised_steps": revised}
        return {"verdict": "escalate", "reason": "Failed checks with no retry path", "revised_steps": []}

    if missing_tools:
        base_input = {
            "dossier_id": dossier.id,
            "doc_no": dossier.doc_no,
            "title": dossier.title,
            "query": dossier.title,
        }
        revised = [
            {
                "id": f"miss-{i + 1}",
                "tool": name,
                "parallel_group": None,
                "depends_on": [],
                "tool_input": dict(base_input),
            }
            for i, name in enumerate(sorted(missing_tools))
        ]
        return {"verdict": "revise", "reason": "Missing planned tools", "revised_steps": revised}

    return {"verdict": "sufficient", "reason": "All checks passed", "revised_steps": []}


async def reflect_on_results(
    dossier: Dossier,
    plan: dict[str, Any],
    checks: list[dict[str, Any]],
    observations: list[str],
    tools: list[dict[str, Any]],
) -> ReflectionResult:
    """LLM reflection on execution results; fallback to rule-based verdict."""
    tool_names = {t["name"] for t in tools}
    checks_summary = "\n".join(
        f"- {c.get('label', c.get('tool'))}: {c.get('status')} — {c.get('desc', '')}" for c in checks
    )
    messages = [
        {
            "role": "system",
            "content": (
                "You are an EVN Hanoi HDTV appraisal critic. "
                f"Review tool results and respond ONLY with JSON:\n{REFLECT_SCHEMA_HINT}\n"
                "Use verdict 'revise' only if more tools are needed; 'escalate' for high-risk blockers."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Dossier: {dossier.title} ({dossier.doc_no})\n"
                f"Plan goal: {plan.get('goal', '')}\n"
                f"Checks:\n{checks_summary}\n\n"
                f"Observations:\n" + "\n".join(observations[-10:])
            ),
        },
    ]

    try:
        raw = await llm_call(AgentRole.REFLECTOR, messages, response_format_json=True)
        result = json.loads(raw) if isinstance(raw, str) else raw
        if not isinstance(result, dict):
            raise TypeError("Reflection must be a JSON object")

        verdict: ReflectionVerdict = result.get("verdict", "sufficient")
        if verdict not in ("sufficient", "revise", "escalate"):
            verdict = "sufficient"

        revised_steps = result.get("revised_steps") or []
        if verdict == "revise" and revised_steps:
            mini_plan = {"steps": revised_steps}
            if not validate_plan(mini_plan, tool_names):
                logger.warning("LLM revised_steps invalid, using rule-based reflection")
                return build_fallback_reflection(checks, plan, tools, dossier)

        return {
            "verdict": verdict,
            "reason": result.get("reason", ""),
            "revised_steps": revised_steps,
        }
    except (json.JSONDecodeError, TypeError) as exc:
        logger.warning("Invalid reflection JSON: %s", exc)

    return build_fallback_reflection(checks, plan, tools, dossier)
