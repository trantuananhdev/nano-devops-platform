"""T-20: Feedback API — user ratings + learning loop stats."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.feedback import FeedbackCreate, FeedbackOut, FeedbackStats
from app.services import feedback_service

router = APIRouter()


@router.post(
    "/dossiers/{dossier_id}/feedback",
    response_model=FeedbackOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_feedback(
    dossier_id: int,
    body: FeedbackCreate,
    session: AsyncSession = Depends(get_db),
) -> FeedbackOut:
    """Submit 👍/👎 feedback on the latest (or specified) appraisal result."""
    try:
        row, _chroma_degraded = await feedback_service.submit_feedback(
            session,
            dossier_id,
            feedback_type=body.feedback_type,
            comment=body.comment,
            user_id=body.user_id,
            appraisal_result_id=body.appraisal_result_id,
            corrected_risk_level=body.corrected_risk_level,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

    return FeedbackOut.model_validate(row)


@router.get("/feedback/stats", response_model=FeedbackStats)
async def feedback_stats(
    session: AsyncSession = Depends(get_db),
) -> FeedbackStats:
    """Aggregate feedback counts for admin / agent intelligence views."""
    stats = await feedback_service.get_feedback_stats(session)
    return FeedbackStats(**stats)
