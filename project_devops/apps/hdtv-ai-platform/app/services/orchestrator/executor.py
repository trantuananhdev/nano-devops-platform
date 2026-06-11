"""T-17/T-18: Execute plan steps with parallel_group batching."""

import json
import logging
from typing import Any, Awaitable, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AgentMemory, AiAuditLog, Dossier
from app.services.orchestrator.chain_executor import get_chained_steps
from app.services.orchestrator.helpers import build_check, normalize_tool_input
from app.services.pubsub import publish_event
from app.services.tools.base import execute_tool
from app.services.tools.batch_executor import execute_parallel

logger = logging.getLogger(__name__)

SaveMemoryFn = Callable[..., Awaitable[None]]


def _topological_steps(steps: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Order steps by depends_on."""
    by_id = {s["id"]: s for s in steps}
    ordered: list[dict[str, Any]] = []
    done: set[str] = set()

    while len(ordered) < len(steps):
        progressed = False
        for step in steps:
            if step["id"] in done:
                continue
            deps = step.get("depends_on") or []
            if all(d in done or d not in by_id for d in deps):
                ordered.append(step)
                done.add(step["id"])
                progressed = True
        if not progressed:
            for step in steps:
                if step["id"] not in done:
                    ordered.append(step)
                    done.add(step["id"])
            break
    return ordered


def _build_execution_batches(steps: list[dict[str, Any]]) -> list[list[dict[str, Any]]]:
    """
    Split topologically valid steps into sequential or parallel execution batches.

    Ready steps sharing the same non-null ``parallel_group`` run together when 2+ are ready.
    """
    ordered = _topological_steps(steps)
    by_id = {s["id"]: s for s in ordered}
    done: set[str] = set()
    remaining = list(ordered)
    batches: list[list[dict[str, Any]]] = []

    while remaining:
        ready = [
            s
            for s in remaining
            if all(d in done or d not in by_id for d in (s.get("depends_on") or []))
        ]
        if not ready:
            ready = [remaining[0]]

        pg_groups: dict[str, list[dict[str, Any]]] = {}
        solo: list[dict[str, Any]] = []
        for step in ready:
            pg = step.get("parallel_group")
            if pg:
                pg_groups.setdefault(pg, []).append(step)
            else:
                solo.append(step)

        parallel_batch = next((members for members in pg_groups.values() if len(members) >= 2), None)
        if parallel_batch:
            batch = parallel_batch
        elif pg_groups:
            batch = [next(iter(pg_groups.values()))[0]]
        else:
            batch = [solo[0] if solo else ready[0]]

        batches.append(batch)
        batch_ids = {s["id"] for s in batch}
        for s in batch:
            done.add(s["id"])
        remaining = [s for s in remaining if s["id"] not in batch_ids]

    return batches


async def _record_tool_result(
    session: AsyncSession,
    dossier: Dossier,
    task_id: str,
    plan_step: dict[str, Any],
    tool_name: str,
    tool_input: dict[str, Any],
    output: dict[str, Any],
    elapsed_ms: int,
    step_num: int,
    *,
    save_memory: SaveMemoryFn,
    parallel_group: str | None = None,
    wall_time_ms: int | None = None,
) -> tuple[dict[str, Any], str]:
    """Persist audit log, memory observation, checks, and pubsub events for one tool."""
    audit = AiAuditLog(
        task_id=task_id,
        tool_name=tool_name,
        execution_time_ms=elapsed_ms,
        inputs=tool_input,
        outputs=output,
        # T-30: Audit correlation — link row to the plan step that triggered it
        plan_step_id=plan_step.get("id"),
        # T-30: Error taxonomy — None on success, filled from output on error
        error_type=str(output.get("error_type")) if output.get("error_type") else None,
    )
    session.add(audit)
    await session.commit()

    check = build_check(tool_name, output)
    obs_text = f"{tool_name}: {json.dumps(output, ensure_ascii=False)}"

    await session.execute(
        AgentMemory.__table__.update()
        .where(AgentMemory.dossier_id == dossier.id)
        .where(AgentMemory.step == step_num)
        .values(observation=json.dumps(output, ensure_ascii=False))
    )
    await session.commit()

    result_event: dict[str, Any] = {
        "type": "tool_result",
        "task_id": task_id,
        "tool_name": tool_name,
        "outputs": output,
        "execution_time_ms": elapsed_ms,
    }
    if parallel_group:
        result_event["parallel_group"] = parallel_group
    if wall_time_ms is not None:
        result_event["parallel_wall_time_ms"] = wall_time_ms

    await publish_event(dossier.id, result_event)
    await publish_event(
        dossier.id,
        {
            "type": "step_completed",
            "task_id": task_id,
            "plan_step_id": plan_step.get("id"),
            "tool_name": tool_name,
            "status": check.get("status"),
            "parallel_group": parallel_group,
        },
    )
    return check, obs_text


async def _run_tool_with_audit(
    session: AsyncSession,
    dossier: Dossier,
    task_id: str,
    plan_step: dict[str, Any],
    tool_name: str,
    tool_input: dict[str, Any],
    step_num: int,
    *,
    save_memory: SaveMemoryFn,
    thought: str | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str, int]:
    """Execute one tool, persist audit/memory/events; return (output, check, obs_text, step_num)."""
    await save_memory(
        session=session,
        dossier_id=dossier.id,
        step=step_num,
        thought=thought or f"Executing plan step {plan_step.get('id')}: {tool_name}",
        action="tool_call",
        tool_name=tool_name,
        tool_input=tool_input,
    )

    await publish_event(
        dossier.id,
        {
            "type": "tool_executing",
            "task_id": task_id,
            "tool_name": tool_name,
            "inputs": tool_input,
            "plan_step_id": plan_step.get("id"),
            "chained_from": tool_input.get("chained_from"),
        },
    )

    output, elapsed_ms = await execute_tool(tool_name, tool_input)
    check, obs_text = await _record_tool_result(
        session,
        dossier,
        task_id,
        plan_step,
        tool_name,
        tool_input,
        output,
        elapsed_ms,
        step_num,
        save_memory=save_memory,
    )
    return output, check, obs_text, step_num


async def _execute_chained_tools(
    session: AsyncSession,
    dossier: Dossier,
    task_id: str,
    parent_tool: str,
    parent_output: dict[str, Any],
    parent_input: dict[str, Any],
    step_num: int,
    *,
    save_memory: SaveMemoryFn,
    parent_step_id: str | None = None,
) -> tuple[list[dict[str, Any]], list[str], int]:
    """Run tool_configs chains_to targets after parent_tool completes (T-21)."""
    chained = await get_chained_steps(
        parent_tool,
        parent_output,
        dossier,
        parent_input=parent_input,
    )
    checks: list[dict[str, Any]] = []
    observations: list[str] = []
    for chained_tool, chained_input in chained:
        step_num += 1
        chain_step = {
            "id": f"chain-{parent_step_id or parent_tool}-{chained_tool}",
            "tool": chained_tool,
            "depends_on": [parent_step_id] if parent_step_id else [],
        }
        thought = (
            f"Chained from {parent_tool} → {chained_tool} "
            f"(mapping={chained_input.get('chain_mapping')})"
        )
        _, check, obs_text, step_num = await _run_tool_with_audit(
            session,
            dossier,
            task_id,
            chain_step,
            chained_tool,
            chained_input,
            step_num,
            save_memory=save_memory,
            thought=thought,
        )
        checks.append(check)
        observations.append(obs_text)
    return checks, observations, step_num


async def _execute_single_step(
    session: AsyncSession,
    dossier: Dossier,
    task_id: str,
    plan_step: dict[str, Any],
    step_num: int,
    *,
    save_memory: SaveMemoryFn,
) -> tuple[list[dict[str, Any]], list[str], int]:
    tool_name = plan_step["tool"]
    tool_input = normalize_tool_input(dossier, plan_step.get("tool_input"))

    output, check, obs_text, step_num = await _run_tool_with_audit(
        session,
        dossier,
        task_id,
        plan_step,
        tool_name,
        tool_input,
        step_num,
        save_memory=save_memory,
    )
    checks = [check]
    observations = [obs_text]

    chain_checks, chain_obs, step_num = await _execute_chained_tools(
        session,
        dossier,
        task_id,
        tool_name,
        output,
        tool_input,
        step_num,
        save_memory=save_memory,
        parent_step_id=plan_step.get("id"),
    )
    checks.extend(chain_checks)
    observations.extend(chain_obs)
    return checks, observations, step_num


async def _execute_parallel_batch(
    session: AsyncSession,
    dossier: Dossier,
    task_id: str,
    batch: list[dict[str, Any]],
    start_step_num: int,
    *,
    save_memory: SaveMemoryFn,
) -> tuple[list[dict[str, Any]], list[str], int]:
    parallel_group = batch[0].get("parallel_group")
    tool_calls: list[dict[str, Any]] = []
    normalized_inputs: list[dict[str, Any]] = []
    step_nums: list[int] = []
    step_num = start_step_num

    for plan_step in batch:
        step_num += 1
        step_nums.append(step_num)
        tool_name = plan_step["tool"]
        tool_input = normalize_tool_input(dossier, plan_step.get("tool_input"))
        normalized_inputs.append(tool_input)
        thought = (
            f"Executing plan step {plan_step.get('id')}: {tool_name} "
            f"(parallel_group={parallel_group})"
        )

        await save_memory(
            session=session,
            dossier_id=dossier.id,
            step=step_num,
            thought=thought,
            action="tool_call",
            tool_name=tool_name,
            tool_input=tool_input,
        )

        await publish_event(
            dossier.id,
            {
                "type": "tool_executing",
                "task_id": task_id,
                "tool_name": tool_name,
                "inputs": tool_input,
                "plan_step_id": plan_step.get("id"),
                "parallel_group": parallel_group,
            },
        )
        tool_calls.append({"tool_name": tool_name, "tool_input": tool_input})

    results, wall_ms = await execute_parallel(tool_calls)

    checks: list[dict[str, Any]] = []
    observations: list[str] = []
    for plan_step, (tool_name, output, elapsed_ms), sn, tool_input in zip(
        batch, results, step_nums, normalized_inputs
    ):
        check, obs_text = await _record_tool_result(
            session,
            dossier,
            task_id,
            plan_step,
            tool_name,
            tool_input,
            output,
            elapsed_ms,
            sn,
            save_memory=save_memory,
            parallel_group=parallel_group,
            wall_time_ms=wall_ms if len(batch) > 1 else None,
        )
        checks.append(check)
        observations.append(obs_text)

        chain_checks, chain_obs, step_num = await _execute_chained_tools(
            session,
            dossier,
            task_id,
            tool_name,
            output,
            tool_input,
            step_num,
            save_memory=save_memory,
            parent_step_id=plan_step.get("id"),
        )
        checks.extend(chain_checks)
        observations.extend(chain_obs)

    if len(batch) > 1:
        logger.info(
            "Parallel group '%s' finished: %d tools in %dms wall time",
            parallel_group,
            len(batch),
            wall_ms,
        )

    return checks, observations, step_num


async def execute_plan_steps(
    session: AsyncSession,
    dossier: Dossier,
    task_id: str,
    plan: dict[str, Any],
    *,
    save_memory: SaveMemoryFn,
    start_step: int = 0,
) -> tuple[list[dict[str, Any]], list[str], int]:
    """
    Run plan steps respecting parallel_group batches.

    Each tool call writes ai_audit_logs and AgentMemory.
    Returns (checks, observations, last_step_number).
    """
    checks: list[dict[str, Any]] = []
    observations: list[str] = []
    step_num = start_step
    batches = _build_execution_batches(plan.get("steps", []))

    for batch in batches:
        if len(batch) == 1:
            new_checks, new_obs, step_num = await _execute_single_step(
                session, dossier, task_id, batch[0], step_num + 1, save_memory=save_memory
            )
        else:
            new_checks, new_obs, step_num = await _execute_parallel_batch(
                session, dossier, task_id, batch, step_num, save_memory=save_memory
            )
        checks.extend(new_checks)
        observations.extend(new_obs)

    return checks, observations, step_num
