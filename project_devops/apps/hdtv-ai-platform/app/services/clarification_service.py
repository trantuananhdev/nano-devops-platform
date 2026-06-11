"""T-22: Human-in-the-loop clarification — detect conflicts, pause, resume."""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AgentClarification, AiAuditLog, ClarificationStatus, Dossier
from app.services.pubsub import publish_event

logger = logging.getLogger(__name__)

_FINANCIAL_TOOLS = frozenset({"ErpBudgetCheck", "ErpInventoryCheck"})


class ClarificationPaused(Exception):
    """Raised when appraisal pauses for human input."""

    def __init__(self, clarification_id: int):
        self.clarification_id = clarification_id
        super().__init__(f"Appraisal paused for clarification {clarification_id}")


def detect_tool_conflict(checks: list[dict[str, Any]]) -> dict[str, Any] | None:
    """Detect conflicting financial tool results requiring human prioritization."""
    by_tool = {c["tool"]: c for c in checks if c.get("tool")}
    budget = by_tool.get("ErpBudgetCheck")
    inventory = by_tool.get("ErpInventoryCheck")

    if (
        budget
        and inventory
        and budget.get("status") == "fail"
        and inventory.get("status") == "fail"
    ):
        return {
            "trigger_type": "tool_conflict",
            "question": (
                "Phát hiện xung đột: cả ngân sách ERP và tồn kho đều có cảnh báo. "
                "Bạn muốn ưu tiên xử lý hướng nào trước khi agent hoàn tất thẩm định?"
            ),
            "options": [
                {"id": "prioritize_budget", "label": "Ưu tiên kiểm tra ngân sách ERP"},
                {"id": "prioritize_inventory", "label": "Ưu tiên kiểm tra tồn kho"},
                {"id": "both_escalate", "label": "Trình cả hai vấn đề lên HĐTV"},
            ],
        }
    return None


def detect_low_confidence(
    reflection: dict[str, Any],
    checks: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Detect uncertain reflection verdict or mixed pass/fail needing human guidance."""
    if reflection.get("verdict") == "escalate":
        return {
            "trigger_type": "low_confidence",
            "question": (
                "Agent không đủ tin cậy để tự quyết định. "
                "Bạn muốn tiếp tục thẩm định theo hướng nào?"
            ),
            "options": [
                {"id": "accept_and_continue", "label": "Chấp nhận kết quả hiện tại và hoàn tất"},
                {"id": "request_more_checks", "label": "Yêu cầu kiểm tra bổ sung trước khi kết luận"},
            ],
        }

    failed = [c for c in checks if c.get("status") == "fail"]
    passed = [c for c in checks if c.get("status") == "pass"]
    if failed and passed and len(failed) >= 1 and len(passed) >= 2:
        return {
            "trigger_type": "low_confidence",
            "question": (
                "Kết quả kiểm tra chưa nhất quán (một số pass, một số fail). "
                "Vui lòng chọn hướng xử lý:"
            ),
            "options": [
                {"id": "accept_and_continue", "label": "Chấp nhận và hoàn tất thẩm định"},
                {"id": "request_more_checks", "label": "Yêu cầu agent kiểm tra lại các mục fail"},
            ],
        }
    return None


async def pause_appraisal(
    session: AsyncSession,
    dossier: Dossier,
    task_id: str,
    trigger: dict[str, Any],
    resume_state: dict[str, Any],
) -> AgentClarification:
    """Persist clarification row, emit WS event, and signal pause to orchestrator."""
    row = AgentClarification(
        dossier_id=dossier.id,
        task_id=task_id,
        question=trigger["question"],
        options=trigger["options"],
        status=ClarificationStatus.pending.value,
        trigger_type=trigger.get("trigger_type"),
        resume_state=resume_state,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)

    await publish_event(
        dossier.id,
        {
            "type": "clarification_needed",
            "task_id": task_id,
            "clarification_id": row.id,
            "question": row.question,
            "options": row.options,
            "trigger_type": row.trigger_type,
        },
    )
    logger.info(
        "Appraisal paused for clarification %d (dossier=%d, trigger=%s)",
        row.id,
        dossier.id,
        row.trigger_type,
    )
    raise ClarificationPaused(row.id)


async def get_pending_clarifications(
    session: AsyncSession,
    *,
    dossier_id: int | None = None,
) -> list[AgentClarification]:
    stmt = (
        select(AgentClarification)
        .where(AgentClarification.status == ClarificationStatus.pending.value)
        .order_by(AgentClarification.created_at.desc())
    )
    if dossier_id is not None:
        stmt = stmt.where(AgentClarification.dossier_id == dossier_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


async def get_clarification(
    session: AsyncSession,
    clarification_id: int,
) -> AgentClarification | None:
    return await session.get(AgentClarification, clarification_id)


async def submit_answer(
    session: AsyncSession,
    clarification_id: int,
    answer_id: str,
    comment: str | None = None,
) -> AgentClarification:
    row = await get_clarification(session, clarification_id)
    if not row:
        raise ValueError(f"Clarification {clarification_id} not found")
    if row.status != ClarificationStatus.pending.value:
        raise ValueError(f"Clarification {clarification_id} is not pending")

    valid_ids = {opt.get("id") for opt in (row.options or []) if isinstance(opt, dict)}
    if answer_id not in valid_ids:
        raise ValueError(f"Invalid answer_id: {answer_id}")

    answer_text = answer_id
    if comment:
        answer_text = f"{answer_id}|{comment.strip()}"

    row.answer = answer_text
    row.status = ClarificationStatus.answered.value
    row.answered_at = datetime.now(timezone.utc)
    await session.commit()
    await session.refresh(row)

    session.add(
        AiAuditLog(
            task_id=row.task_id,
            tool_name="ClarificationAnswer",
            execution_time_ms=0,
            inputs={"clarification_id": clarification_id, "answer_id": answer_id, "comment": comment},
            outputs={"status": "answered"},
        )
    )
    await session.commit()
    return row


def apply_clarification_answer(
    clarification: AgentClarification,
    checks: list[dict[str, Any]],
    observations: list[str],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Incorporate human choice into observations and optionally adjust check emphasis."""
    answer = clarification.answer or ""
    answer_id = answer.split("|", 1)[0]
    label_map = {
        opt.get("id"): opt.get("label")
        for opt in (clarification.options or [])
        if isinstance(opt, dict)
    }
    label = label_map.get(answer_id, answer_id)
    observations = list(observations)
    observations.append(f"Human clarification ({clarification.trigger_type}): {label}")

    if answer_id == "both_escalate":
        observations.append("Human directive: escalate both financial issues to HĐTV.")
    elif answer_id == "prioritize_budget":
        observations.append("Human directive: prioritize ERP budget review in final report.")
    elif answer_id == "prioritize_inventory":
        observations.append("Human directive: prioritize inventory waste review in final report.")
    elif answer_id == "request_more_checks":
        observations.append("Human directive: re-check failed items before finalizing.")

    return checks, observations
