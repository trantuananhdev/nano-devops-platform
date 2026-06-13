import json
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    AgentPlan,
    AgentPlanStatus,
    AiAuditLog,
    AgentMemory,
    Alert,
    AlertStatus,
    AppraisalResult,
    ClarificationStatus,
    Dossier,
    DossierStatus,
    RiskLevel,
    RiskRule,
    User,
    UserRole,
)
from app.services import search_service
from app.services import clarification_service
from app.services.clarification_service import ClarificationPaused
from app.services.llm_router import AgentRole, llm_call
from app.core.context_manager import trim_observations
from app.core.metrics import AGENT_PLANS, CRITIC_REJECTIONS
from app.services.memory import vector_store as mem_store
from app.services.memory import retriever as mem_retriever
from app.services.memory.retriever import build_preference_context
from app.services.memory import preference_service
from app.services.orchestrator import critic as plan_critic
from app.services.orchestrator import executor as plan_executor
from app.services.orchestrator import planner as plan_planner
from app.services.orchestrator import reflector as plan_reflector
from app.services.orchestrator.types import CriticResult
from app.services.orchestrator import prompt_builder
from app.services.orchestrator.helpers import build_check, normalize_tool_input
from app.services.orchestrator.planner import validate_plan
from app.services.pubsub import publish_event
from app.services.tools.base import execute_tool, list_tools_dynamic

logger = logging.getLogger(__name__)


async def _resolve_user_role(session: AsyncSession, user_id: int | None) -> UserRole:
    """Load role from users table; default to specialist when absent."""
    if user_id is None:
        return UserRole.specialist
    user = await session.get(User, user_id)
    if not user:
        logger.warning("User %d not found — defaulting to specialist profile", user_id)
        return UserRole.specialist
    return user.role


_RULE_SAFE_BUILTINS: dict[str, Any] = {
    "len": len,
    "any": any,
    "all": all,
    "sum": sum,
    "min": min,
    "max": max,
    "bool": bool,
    "int": int,
    "str": str,
    "list": list,
    "dict": dict,
    "True": True,
    "False": False,
    "None": None,
}


def _eval_rule_expression(expression: str, checks: list[dict[str, Any]]) -> bool:
    """
    Evaluate a risk-rule condition expression in a restricted sandbox.

    Only whitelisted builtins are available; ``__builtins__`` is fully blocked.
    Context exposes:
      - ``checks``        — list of check dicts
      - ``failed``        — pre-filtered list of failed checks
      - ``passed``        — pre-filtered list of passed checks
      - ``failed_tools``  — set of tool names with status==fail
    """
    failed = [c for c in checks if c.get("status") == "fail"]
    passed = [c for c in checks if c.get("status") == "pass"]
    failed_tools = {c.get("tool", "") for c in failed}
    context: dict[str, Any] = {
        "__builtins__": {},
        "checks": checks,
        "failed": failed,
        "passed": passed,
        "failed_tools": failed_tools,
    }
    context.update(_RULE_SAFE_BUILTINS)
    return bool(eval(expression, context))  # noqa: S307 — guarded by whitelist above


async def _execute_risk_rules(checks: list[dict[str, Any]], session: AsyncSession) -> RiskLevel:
    """Evaluate risk using configurable rules from database."""
    result = await session.execute(
        select(RiskRule).where(RiskRule.is_active.is_(True)).order_by(RiskRule.priority.desc())
    )
    rules = list(result.scalars().all())

    if not rules:
        for check in checks:
            if check.get("status") == "fail":
                label = check.get("label", "")
                if "ERP" in label or "ngân sách" in label.lower() or "tồn kho" in label.lower():
                    return RiskLevel.high
                return RiskLevel.medium
        return RiskLevel.low

    for rule in rules:
        try:
            if _eval_rule_expression(rule.condition_expression, checks):
                logger.info("Risk rule '%s' matched: %s", rule.name, rule.description)
                return rule.risk_level
        except Exception as exc:
            logger.error("Failed to evaluate risk rule '%s': %s", rule.name, exc)

    return RiskLevel.low


async def _save_memory(
    session: AsyncSession,
    dossier_id: int,
    step: int,
    thought: str,
    action: str,
    tool_name: str | None = None,
    tool_input: dict[str, Any] | None = None,
    observation: str | None = None,
) -> None:
    """Save agent reasoning to PostgreSQL and upsert to Chroma vector store (T-15)."""
    memory = AgentMemory(
        dossier_id=dossier_id,
        step=step,
        thought=thought,
        action=action,
        tool_name=tool_name,
        tool_input=tool_input or {},
        observation=observation,
    )
    session.add(memory)
    await session.commit()
    await session.refresh(memory)

    embedding_id = await mem_store.upsert_memory(
        dossier_id=dossier_id,
        step=step,
        thought=thought,
        observation=observation,
        tool_name=tool_name,
        memory_id=f"mem-{dossier_id}-{step}-{memory.id}",
    )
    if embedding_id:
        await session.execute(
            AgentMemory.__table__.update()
            .where(AgentMemory.id == memory.id)
            .values(embedding_id=embedding_id)
        )
        await session.commit()
        logger.debug("Chroma embedding_id stored for step %d (mem_id=%d): %s", step, memory.id, embedding_id)


async def _persist_agent_plan(
    session: AsyncSession,
    dossier_id: int,
    plan_json: dict[str, Any],
    revision: int,
    status: str,
) -> AgentPlan:
    """Save agent plan row for audit trail."""
    row = AgentPlan(
        dossier_id=dossier_id,
        plan_json=plan_json,
        revision=revision,
        status=status,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return row


async def _run_plan_execute_reflect(
    session: AsyncSession,
    dossier: Dossier,
    task_id: str,
    tools: list[dict[str, Any]],
    pref_context: str,
    user_id: int | None = None,
    role: UserRole | None = None,
) -> tuple[list[dict[str, Any]], list[str], int]:
    """T-17: planner → executor → reflector loop with max 2 revisions."""
    tool_names = {t["name"] for t in tools}
    query_text = f"{dossier.title} {dossier.doc_no}"
    memory_chunks = await mem_retriever.retrieve_relevant_memories(
        session=session,
        dossier_id=dossier.id,
        query=query_text,
    )
    memory_context = "\n".join(c["document"] for c in memory_chunks) if memory_chunks else ""

    feedback_lessons = await mem_retriever.retrieve_feedback_lessons(
        query_text, unit=dossier.unit, session=session
    )
    feedback_lessons_context = mem_retriever.build_feedback_lessons_context(feedback_lessons)

    plan = await plan_planner.create_plan(
        dossier,
        tools,
        role=role,
        pref_context=pref_context,
        memory_context=memory_context,
        feedback_lessons_context=feedback_lessons_context,
        revision=0,
    )

    if not validate_plan(plan, tool_names):
        raise ValueError("Plan validation failed after create_plan")

    plan_row = await _persist_agent_plan(
        session, dossier.id, plan, revision=0, status=AgentPlanStatus.executing.value
    )

    await publish_event(
        dossier.id,
        {
            "type": "plan_created",
            "task_id": task_id,
            "plan_id": plan_row.id,
            "goal": plan.get("goal"),
            "step_count": len(plan.get("steps", [])),
            "steps": plan.get("steps", []),
        },
    )

    checks: list[dict[str, Any]] = []
    observations: list[str] = []
    step_num = 0
    max_revisions = int(plan.get("max_revisions", 2))
    revision = 0
    current_plan = plan

    while True:
        new_checks, new_obs, step_num = await plan_executor.execute_plan_steps(
            session,
            dossier,
            task_id,
            current_plan,
            save_memory=_save_memory,
            start_step=step_num,
        )
        checks.extend(new_checks)
        observations.extend(new_obs)

        if revision == 0:
            resume_state = _build_clarification_resume_state(
                user_id=user_id,
                checks=checks,
                observations=observations,
                last_step=step_num,
                current_plan=current_plan,
                revision=revision,
                pref_context=pref_context,
                tools=tools,
            )
            await _maybe_pause_for_clarification(
                session,
                dossier,
                task_id,
                clarification_service.detect_tool_conflict(checks),
                resume_state,
            )

        reflection = await plan_reflector.reflect_on_results(
            dossier, current_plan, checks, observations, tools
        )
        verdict = reflection.get("verdict", "sufficient")
        logger.info("Reflection verdict: %s — %s", verdict, reflection.get("reason", ""))
        AGENT_PLANS.labels(verdict=verdict).inc()

        if revision == 0 and verdict in ("sufficient", "escalate"):
            resume_state = _build_clarification_resume_state(
                user_id=user_id,
                checks=checks,
                observations=observations,
                last_step=step_num,
                current_plan=current_plan,
                revision=revision,
                pref_context=pref_context,
                tools=tools,
            )
            low_conf = clarification_service.detect_low_confidence(reflection, checks)
            if low_conf and (verdict == "escalate" or low_conf.get("trigger_type") == "low_confidence"):
                await _maybe_pause_for_clarification(
                    session, dossier, task_id, low_conf, resume_state
                )

        if verdict == "sufficient" or verdict == "escalate":
            await _persist_agent_plan(
                session,
                dossier.id,
                current_plan,
                revision=revision,
                status=AgentPlanStatus.completed.value,
            )
            break

        if verdict == "revise" and revision < max_revisions:
            revised_steps = reflection.get("revised_steps") or []
            if not revised_steps:
                break
            revision += 1
            current_plan = {
                **current_plan,
                "steps": revised_steps,
                "goal": current_plan.get("goal", "") + f" (revision {revision})",
            }
            plan_row = await _persist_agent_plan(
                session,
                dossier.id,
                current_plan,
                revision=revision,
                status=AgentPlanStatus.revised.value,
            )
            await publish_event(
                dossier.id,
                {
                    "type": "plan_revised",
                    "task_id": task_id,
                    "plan_id": plan_row.id,
                    "revision": revision,
                    "step_count": len(revised_steps),
                    "reason": reflection.get("reason", ""),
                },
            )
            continue

        break

    return checks, observations, step_num


def _build_clarification_resume_state(
    *,
    user_id: int | None,
    checks: list[dict[str, Any]],
    observations: list[str],
    last_step: int,
    current_plan: dict[str, Any],
    revision: int,
    pref_context: str,
    tools: list[dict[str, Any]],
) -> dict[str, Any]:
    # Trim observations before persisting to JSONB to prevent row bloat.
    # The full history is already stored in AgentMemory rows; resume only
    # needs the last few observations to reconstruct context after HITL.
    trimmed_observations = trim_observations(observations, max_tokens=1024)
    return {
        "user_id": user_id,
        "checks": checks,
        "observations": trimmed_observations,
        "last_step": last_step,
        "current_plan": current_plan,
        "revision": revision,
        "pref_context": pref_context,
        "tools": tools,
    }


async def _maybe_pause_for_clarification(
    session: AsyncSession,
    dossier: Dossier,
    task_id: str,
    trigger: dict[str, Any] | None,
    resume_state: dict[str, Any],
) -> None:
    """Pause appraisal when trigger detected and no pending clarification exists."""
    if not trigger:
        return
    pending = await clarification_service.get_pending_clarifications(
        session, dossier_id=dossier.id
    )
    if pending:
        return
    await clarification_service.pause_appraisal(
        session, dossier, task_id, trigger, resume_state
    )


async def _complete_appraisal_from_checks(
    session: AsyncSession,
    dossier: Dossier,
    dossier_id: int,
    task_id: str,
    checks: list[dict[str, Any]],
    observations: list[str],
    last_step: int,
    *,
    role: UserRole | None = None,
    force_high_risk: bool = False,
) -> AppraisalResult:
    """Shared completion path: LLM summary → critic → persist result."""
    llm_messages = [
        {"role": "system", "content": prompt_builder.build_summary_system_prompt(role)},
        {
            "role": "user",
            "content": f"Dossier: {dossier.title}\nObservations:\n" + "\n".join(observations),
        },
    ]
    llm_raw = await llm_call(AgentRole.SUMMARY, llm_messages, response_format_json=False)

    overall_risk = await _execute_risk_rules(checks, session)
    if force_high_risk:
        overall_risk = RiskLevel.high

    report_md, resolution_md, overall_risk, checks, observations, critic_verdict = await _run_critic_loop(
        session,
        dossier,
        task_id,
        checks,
        observations,
        overall_risk,
        llm_raw,
        last_step,
        role=role,
    )

    dossier.risk_level = overall_risk

    if overall_risk == RiskLevel.high:
        alert = Alert(
            dossier_id=dossier_id,
            title=f"Rủi ro cao: {dossier.doc_no}",
            severity="high",
            source="AI Appraisal",
            description=f"Cảnh báo rủi ro cao cho {dossier.doc_no}: vượt ngưỡng kiểm tra ERP/pháp lý",
            status=AlertStatus.open,
        )
        session.add(alert)
        await publish_event(
            dossier_id,
            {"type": "risk_flagged", "task_id": task_id, "risk": overall_risk.value},
        )

    result = AppraisalResult(
        dossier_id=dossier_id,
        overall_risk=overall_risk,
        report_md=report_md,
        resolution_md=resolution_md,
        checks={"items": checks},
        critic_verdict=critic_verdict,
    )
    session.add(result)
    dossier.status = DossierStatus.needs_revision if overall_risk == RiskLevel.high else DossierStatus.approved
    await session.commit()
    await session.refresh(result)
    await session.refresh(dossier)

    await search_service.index_dossier(search_service.dossier_to_doc(dossier))

    await publish_event(
        dossier_id,
        {
            "type": "completed",
            "task_id": task_id,
            "overall_risk": overall_risk.value,
            "appraisal_id": result.id,
        },
    )
    return result


async def resume_appraisal(
    session: AsyncSession,
    clarification_id: int,
) -> AppraisalResult:
    """T-22: Resume paused appraisal after human clarification answer."""
    clar = await clarification_service.get_clarification(session, clarification_id)
    if not clar:
        raise ValueError(f"Clarification {clarification_id} not found")
    if clar.status != ClarificationStatus.answered.value:
        raise ValueError(f"Clarification {clarification_id} is not answered")

    state = clar.resume_state or {}
    dossier = await session.get(Dossier, clar.dossier_id)
    if not dossier:
        raise ValueError(f"Dossier {clar.dossier_id} not found")

    task_id = clar.task_id
    dossier.status = DossierStatus.appraising
    await session.commit()

    await publish_event(
        dossier.id,
        {
            "type": "clarification_answered",
            "task_id": task_id,
            "clarification_id": clarification_id,
            "answer": clar.answer,
        },
    )

    checks = list(state.get("checks", []))
    observations = list(state.get("observations", []))
    last_step = int(state.get("last_step", 0))
    checks, observations = clarification_service.apply_clarification_answer(
        clar, checks, observations
    )

    answer_id = (clar.answer or "").split("|", 1)[0]
    if answer_id == "request_more_checks":
        checks, new_obs, last_step = await _reexecute_failed_checks(
            session, dossier, task_id, checks, last_step
        )
        observations.extend(new_obs)

    force_high = answer_id == "both_escalate"
    resume_role = prompt_builder.normalize_role(
        await _resolve_user_role(session, state.get("user_id"))
    )
    return await _complete_appraisal_from_checks(
        session,
        dossier,
        dossier.id,
        task_id,
        checks,
        observations,
        last_step,
        role=resume_role,
        force_high_risk=force_high,
    )


async def _run_legacy_react_loop(
    session: AsyncSession,
    dossier: Dossier,
    task_id: str,
    tools: list[dict[str, Any]],
    system_prompt: str,
) -> tuple[list[dict[str, Any]], list[str], int]:
    """Legacy sequential ReAct loop when plan orchestration is unavailable."""
    checks: list[dict[str, Any]] = []
    observations: list[str] = []
    step = 0
    max_steps = 10

    while step < max_steps:
        step += 1

        conversation = [{"role": "system", "content": system_prompt}]

        query_text = f"{dossier.title} {dossier.doc_no}"
        memory_chunks = await mem_retriever.retrieve_relevant_memories(
            session=session,
            dossier_id=dossier.id,
            query=query_text,
        )

        if memory_chunks:
            mem_text = "\n".join(c["document"] for c in memory_chunks)
            context = (
                f"Dossier: {dossier.title}\n"
                f"Doc No: {dossier.doc_no}\n\n"
                f"Relevant memory context (top retrieved):\n{mem_text}"
            )
            if observations:
                context += "\n\nLatest raw observations:\n" + "\n".join(observations[-3:])
            conversation.append({"role": "user", "content": context})
        elif observations:
            context = f"Dossier: {dossier.title}\n\nPrevious observations:\n" + "\n".join(observations)
            conversation.append({"role": "user", "content": context})
        else:
            conversation.append({
                "role": "user",
                "content": f"Please assess this dossier: {dossier.title} (Doc No: {dossier.doc_no}). What should we check first?",
            })

        try:
            llm_response = await llm_call(AgentRole.EXECUTOR, conversation, response_format_json=True)
            logger.info("LLM decision: %s", llm_response)

            try:
                decision = json.loads(llm_response) if isinstance(llm_response, str) else llm_response
            except json.JSONDecodeError:
                logger.warning("LLM returned invalid JSON, using fallback strategy")
                decision = {
                    "thought": "Using fallback strategy - calling tools in sequence",
                    "action": "tool_call",
                    "tool_name": tools[min(step - 1, len(tools) - 1)]["name"],
                    "tool_input": {
                        "dossier_id": dossier.id,
                        "doc_no": dossier.doc_no,
                        "title": dossier.title,
                        "query": dossier.title,
                    },
                }

            thought = decision.get("thought", "No reasoning provided")
            action = decision.get("action", "finish")

            await _save_memory(
                session=session,
                dossier_id=dossier.id,
                step=step,
                thought=thought,
                action=action,
                tool_name=decision.get("tool_name"),
                tool_input=decision.get("tool_input"),
            )

            if action == "finish":
                break
            if action != "tool_call":
                break

            tool_name = decision.get("tool_name")
            if not tool_name:
                break

            tool_input = normalize_tool_input(dossier, decision.get("tool_input"))

            await publish_event(
                dossier.id,
                {"type": "tool_executing", "task_id": task_id, "tool_name": tool_name, "inputs": tool_input},
            )

            output, elapsed_ms = await execute_tool(tool_name, tool_input)

            audit = AiAuditLog(
                task_id=task_id,
                tool_name=tool_name,
                execution_time_ms=elapsed_ms,
                inputs=tool_input,
                outputs=output,
            )
            session.add(audit)
            await session.commit()

            check = build_check(tool_name, output)
            checks.append(check)
            observations.append(f"{tool_name}: {json.dumps(output, ensure_ascii=False)}")

            await session.execute(
                AgentMemory.__table__.update()
                .where(AgentMemory.dossier_id == dossier.id)
                .where(AgentMemory.step == step)
                .values(observation=json.dumps(output, ensure_ascii=False))
            )
            await session.commit()

            await publish_event(
                dossier.id,
                {
                    "type": "tool_result",
                    "task_id": task_id,
                    "tool_name": tool_name,
                    "outputs": output,
                    "execution_time_ms": elapsed_ms,
                },
            )

            called_tool_names = {c["tool"] for c in checks}
            available_tool_names = {t["name"] for t in tools}
            if called_tool_names.issuperset(available_tool_names):
                break

        except Exception:
            logger.exception("Error in legacy agent loop step %d", step)
            if step >= 3:
                break

    return checks, observations, step


def _build_report_drafts(
    dossier: Dossier,
    checks: list[dict[str, Any]],
    overall_risk: RiskLevel,
    llm_raw: str,
    *,
    role: UserRole | None = None,
) -> tuple[str, str]:
    """Build report_md and resolution_md from checks and LLM analysis."""
    report_md = (
        f"# Báo cáo thẩm định AI\n\n"
        f"**Số hiệu**: {dossier.doc_no}\n\n"
        f"**Mức rủi ro**: {overall_risk.value.upper()}\n\n"
        f"**Phương pháp**: Đánh giá tự động bằng Agent AI Plan-Execute-Reflect\n\n"
        f"## Kết quả kiểm tra\n\n"
        + "\n".join(f"- **{c['label']}**: {c['status'].upper()} — {c['desc']}" for c in checks)
        + f"\n\n## Phân tích LLM\n\n{llm_raw}\n"
    )
    resolution_md = prompt_builder.build_resolution_md(role, dossier, overall_risk, checks)
    return report_md, resolution_md


def _merge_checks(existing: list[dict[str, Any]], updates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Replace checks by tool name when re-executing after critic rejection."""
    by_tool = {c.get("tool"): c for c in existing if c.get("tool")}
    for check in updates:
        tool = check.get("tool")
        if tool:
            by_tool[tool] = check
    return list(by_tool.values())


async def _reexecute_failed_checks(
    session: AsyncSession,
    dossier: Dossier,
    task_id: str,
    checks: list[dict[str, Any]],
    start_step: int,
) -> tuple[list[dict[str, Any]], list[str], int]:
    """Re-run tools for failed checks when critic requests revision."""
    failed = [c for c in checks if c.get("status") == "fail" and c.get("tool")]
    if not failed:
        return checks, [], start_step

    steps = [
        {
            "id": f"critic-rev-{i + 1}",
            "tool": check["tool"],
            "parallel_group": None,
            "depends_on": [],
            "tool_input": {
                "dossier_id": dossier.id,
                "doc_no": dossier.doc_no,
                "title": dossier.title,
                "query": f"Critic re-check: {check.get('label', check['tool'])}",
            },
        }
        for i, check in enumerate(failed)
    ]
    mini_plan = {"steps": steps, "goal": "Critic revision — re-execute failed checks"}
    new_checks, new_obs, last_step = await plan_executor.execute_plan_steps(
        session,
        dossier,
        task_id,
        mini_plan,
        save_memory=_save_memory,
        start_step=start_step,
    )
    merged = _merge_checks(checks, new_checks)
    return merged, new_obs, last_step


async def _regenerate_llm_summary(
    dossier: Dossier,
    observations: list[str],
    critic_verdict: CriticResult,
    *,
    role: UserRole | None = None,
) -> str:
    """Regenerate LLM summary incorporating critic feedback."""
    fixes = critic_verdict.get("suggested_fixes") or []
    issues = critic_verdict.get("issues") or []
    feedback = "\n".join(f"- {i}" for i in issues + fixes)

    base = prompt_builder.build_summary_system_prompt(role)
    messages = [
        {
            "role": "system",
            "content": (
                f"{base} Revise the summary to address critic feedback. "
                "Be explicit about failed checks and risk."
            ),
        },
        {
            "role": "user",
            "content": (
                f"Dossier: {dossier.title}\n"
                f"Critic feedback:\n{feedback}\n\n"
                f"Observations:\n" + "\n".join(observations)
            ),
        },
    ]
    return await llm_call(AgentRole.SUMMARY, messages, response_format_json=False)


async def _run_critic_loop(
    session: AsyncSession,
    dossier: Dossier,
    task_id: str,
    checks: list[dict[str, Any]],
    observations: list[str],
    overall_risk: RiskLevel,
    llm_raw: str,
    start_step: int,
    *,
    role: UserRole | None = None,
    max_revisions: int = 2,
) -> tuple[str, str, RiskLevel, list[dict[str, Any]], list[str], CriticResult]:
    """
    T-19: Review drafts with critic; re-execute failed tools or regenerate on rejection.
    Returns final drafts, updated risk/checks/observations, and last critic verdict.
    """
    report_md, resolution_md = _build_report_drafts(
        dossier, checks, overall_risk, llm_raw, role=role
    )
    critic_revision = 0
    last_verdict: CriticResult = {"approved": True, "issues": [], "suggested_fixes": [], "source": "rules"}
    step_num = start_step

    while True:
        verdict = await plan_critic.review_draft(
            report_md,
            checks,
            overall_risk,
            resolution_md=resolution_md,
        )
        last_verdict = verdict

        await publish_event(
            dossier.id,
            {
                "type": "critic_review",
                "task_id": task_id,
                "approved": verdict.get("approved", True),
                "issues": verdict.get("issues", []),
                "suggested_fixes": verdict.get("suggested_fixes", []),
                "revision": critic_revision,
                "source": verdict.get("source", "rules"),
            },
        )

        if verdict.get("approved", True) or critic_revision >= max_revisions:
            break

        critic_revision += 1
        logger.info(
            "Critic rejected draft (revision %d/%d): %s",
            critic_revision,
            max_revisions,
            verdict.get("issues"),
        )

        checks, new_obs, step_num = await _reexecute_failed_checks(
            session, dossier, task_id, checks, step_num
        )
        if new_obs:
            observations.extend(new_obs)
            overall_risk = await _execute_risk_rules(checks, session)

        llm_raw = await _regenerate_llm_summary(dossier, observations, verdict, role=role)
        report_md, resolution_md = _build_report_drafts(
            dossier, checks, overall_risk, llm_raw, role=role
        )

    return report_md, resolution_md, overall_risk, checks, observations, last_verdict


async def run_appraisal(
    session: AsyncSession,
    dossier_id: int,
    task_id: str,
    user_id: int | None = None,
) -> AppraisalResult:
    """Run autonomous appraisal via plan-execute-reflect (T-17) with legacy fallback."""
    dossier = await session.get(Dossier, dossier_id)
    if not dossier:
        raise ValueError(f"Dossier {dossier_id} not found")

    dossier.status = DossierStatus.appraising
    await session.commit()

    await publish_event(dossier_id, {"type": "started", "task_id": task_id, "dossier_id": dossier_id})

    user_role = await _resolve_user_role(session, user_id)
    user_prefs: dict[str, Any] = {}
    if user_id is not None:
        try:
            user_prefs = await preference_service.get_preferences(session, user_id)
        except Exception as exc:
            logger.warning("Could not load user preferences for user %d: %s", user_id, exc)
    pref_context = build_preference_context(user_prefs)
    logger.info(
        "Appraisal profile: user_id=%s role=%s prefs=%s",
        user_id,
        user_role.value,
        list(user_prefs.keys()) if user_prefs else [],
    )

    tools = await list_tools_dynamic()
    if not tools:
        logger.warning("No tools configured in database, using static list")
        tools = [
            {"name": "LegalGraphRAG", "description": "Check legal documents", "category": "legal", "priority": 10},
            {"name": "ErpBudgetCheck", "description": "Check budget in ERP", "category": "financial", "priority": 9},
            {"name": "ErpInventoryCheck", "description": "Check inventory in ERP", "category": "financial", "priority": 8},
            {"name": "DOfficeLookup", "description": "Check document registry", "category": "admin", "priority": 7},
            {"name": "PmisProjectCheck", "description": "Check project schedule", "category": "project", "priority": 6},
        ]

    system_prompt = prompt_builder.build_system_prompt(user_role, tools, user_prefs)

    try:
        checks, observations, last_step = await _run_plan_execute_reflect(
            session,
            dossier,
            task_id,
            tools,
            pref_context,
            user_id=user_id,
            role=user_role,
        )
    except ClarificationPaused:
        raise
    except Exception as exc:
        logger.warning("Plan orchestration failed (%s), falling back to legacy ReAct", exc)
        checks, observations, last_step = await _run_legacy_react_loop(
            session, dossier, task_id, tools, system_prompt
        )

    return await _complete_appraisal_from_checks(
        session,
        dossier,
        dossier_id,
        task_id,
        checks,
        observations,
        last_step,
        role=user_role,
    )
