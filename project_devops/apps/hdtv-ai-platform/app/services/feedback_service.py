"""T-20: Feedback persistence + Chroma learning loop for negative feedback."""

import logging
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AgentFeedback, AppraisalResult, Dossier, RiskLevel
from app.services.memory import vector_store

logger = logging.getLogger(__name__)

_NEGATIVE_TYPES = frozenset({"reject", "adjust"})


async def _latest_appraisal_id(session: AsyncSession, dossier_id: int) -> int | None:
    result = await session.execute(
        select(AppraisalResult.id)
        .where(AppraisalResult.dossier_id == dossier_id)
        .order_by(AppraisalResult.created_at.desc())
        .limit(1)
    )
    row = result.scalar_one_or_none()
    return row


async def submit_feedback(
    session: AsyncSession,
    dossier_id: int,
    *,
    feedback_type: str,
    comment: str | None = None,
    user_id: int | None = None,
    appraisal_result_id: int | None = None,
    corrected_risk_level: str | None = None,
) -> tuple[AgentFeedback, bool]:
    """Persist feedback; embed negative lessons into Chroma when applicable.

    Returns (feedback_row, chroma_degraded).
    """
    dossier = await session.get(Dossier, dossier_id)
    if not dossier:
        raise ValueError("Dossier not found")

    resolved_appraisal_id = appraisal_result_id or await _latest_appraisal_id(session, dossier_id)

    risk_enum: RiskLevel | None = None
    if corrected_risk_level:
        risk_enum = RiskLevel(corrected_risk_level)

    row = AgentFeedback(
        dossier_id=dossier_id,
        appraisal_result_id=resolved_appraisal_id,
        user_id=user_id,
        feedback_type=feedback_type,
        comment=comment,
        corrected_risk_level=risk_enum,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)

    chroma_degraded = False
    if feedback_type in _NEGATIVE_TYPES:
        lesson_doc = _build_lesson_document(
            dossier_id=dossier_id,
            doc_no=dossier.doc_no,
            title=dossier.title,
            unit=dossier.unit,
            feedback_type=feedback_type,
            comment=comment,
            corrected_risk_level=corrected_risk_level,
        )
        embedding_id = await vector_store.upsert_feedback_lesson(
            feedback_id=row.id,
            dossier_id=dossier_id,
            document=lesson_doc,
            unit=dossier.unit,
            feedback_type=feedback_type,
        )
        if embedding_id is None:
            chroma_degraded = True
            logger.warning(
                "Chroma feedback_lessons upsert skipped (degraded) for feedback %d", row.id
            )

    return row, chroma_degraded


def _build_lesson_document(
    *,
    dossier_id: int,
    doc_no: str,
    title: str,
    unit: str,
    feedback_type: str,
    comment: str | None,
    corrected_risk_level: str | None,
) -> str:
    parts = [
        f"[Negative feedback — {feedback_type}]",
        f"Dossier {doc_no}: {title}",
        f"Unit: {unit}",
    ]
    if corrected_risk_level:
        parts.append(f"Corrected risk level: {corrected_risk_level}")
    if comment:
        parts.append(f"User comment: {comment}")
    parts.append(
        "Lesson: avoid repeating this appraisal mistake; prioritize user-corrected risk assessment."
    )
    return "\n".join(parts)


async def get_feedback_stats(session: AsyncSession) -> dict[str, Any]:
    """Aggregate counts from agent_feedbacks table."""
    result = await session.execute(
        select(
            AgentFeedback.feedback_type,
            func.count(AgentFeedback.id),
        ).group_by(AgentFeedback.feedback_type)
    )
    counts: dict[str, int] = {row[0]: row[1] for row in result.all()}
    approve = counts.get("approve", 0)
    reject = counts.get("reject", 0)
    adjust = counts.get("adjust", 0)
    total = approve + reject + adjust

    negative_indexed = await vector_store.count_feedback_lessons()

    return {
        "total": total,
        "approve": approve,
        "reject": reject,
        "adjust": adjust,
        "negative_lessons_indexed": negative_indexed,
        "degraded_chroma": False,
    }
