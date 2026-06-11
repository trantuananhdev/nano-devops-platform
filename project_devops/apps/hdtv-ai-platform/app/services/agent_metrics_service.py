"""T-24: Aggregate agent intelligence metrics from plans, critic, feedback, memory, audit."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import (
    AgentFeedback,
    AgentMemory,
    AgentPlan,
    AiAuditLog,
    AppraisalResult,
)

# Non-tool audit entries — excluded from tool_calls_total
_ADMIN_AUDIT_TOOLS = frozenset({
    "DossierCreate",
    "PdfUpload",
    "WorkflowSave",
    "ClarificationAnswer",
})


def _safe_rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 4)


async def get_agent_metrics(session: AsyncSession) -> dict[str, Any]:
    """Compute Level-4 agent KPIs for the admin intelligence dashboard."""
    total_plans = (
        await session.execute(select(func.count(AgentPlan.id)))
    ).scalar() or 0

    revised_plans = (
        await session.execute(
            select(func.count(AgentPlan.id)).where(AgentPlan.revision > 0)
        )
    ).scalar() or 0

    plan_revision_rate = _safe_rate(revised_plans, total_plans)

    verdict_rows = (
        await session.execute(
            select(AppraisalResult.critic_verdict).where(
                AppraisalResult.critic_verdict.isnot(None)
            )
        )
    ).all()

    total_with_verdict = len(verdict_rows)
    critic_rejections = sum(
        1
        for (verdict,) in verdict_rows
        if isinstance(verdict, dict) and verdict.get("approved") is False
    )
    critic_rejection_rate = _safe_rate(critic_rejections, total_with_verdict)

    total_appraisals = (
        await session.execute(select(func.count(AppraisalResult.id)))
    ).scalar() or 0

    feedback_rows = (
        await session.execute(
            select(AgentFeedback.feedback_type, func.count(AgentFeedback.id)).group_by(
                AgentFeedback.feedback_type
            )
        )
    ).all()
    feedback_counts = {row[0]: row[1] for row in feedback_rows}
    feedback_approve = feedback_counts.get("approve", 0)
    feedback_reject = feedback_counts.get("reject", 0)
    feedback_adjust = feedback_counts.get("adjust", 0)
    feedback_total = feedback_approve + feedback_reject + feedback_adjust

    memory_retrieval_count = (
        await session.execute(select(func.count(AgentMemory.id)))
    ).scalar() or 0

    memories_indexed = (
        await session.execute(
            select(func.count(AgentMemory.id)).where(AgentMemory.embedding_id.isnot(None))
        )
    ).scalar() or 0

    tool_calls_total = (
        await session.execute(
            select(func.count(AiAuditLog.id)).where(
                AiAuditLog.tool_name.notin_(_ADMIN_AUDIT_TOOLS)
            )
        )
    ).scalar() or 0

    return {
        "plan_revision_rate": plan_revision_rate,
        "critic_rejection_rate": critic_rejection_rate,
        "feedback_total": feedback_total,
        "memory_retrieval_count": memory_retrieval_count,
        "total_plans": total_plans,
        "revised_plans": revised_plans,
        "total_appraisals": total_appraisals,
        "critic_rejections": critic_rejections,
        "feedback_approve": feedback_approve,
        "feedback_reject": feedback_reject,
        "feedback_adjust": feedback_adjust,
        "memories_indexed": memories_indexed,
        "tool_calls_total": tool_calls_total,
    }
