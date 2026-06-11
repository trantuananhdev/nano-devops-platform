"""T-22: Human-in-the-loop clarification endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.clarification import ClarificationAnswer, ClarificationOut
from app.services import clarification_service
from app.workers.tasks import resume_appraisal_task

router = APIRouter()


@router.get("/clarifications/pending", response_model=list[ClarificationOut])
async def list_pending_clarifications(
    dossier_id: int | None = Query(default=None, ge=1),
    session: AsyncSession = Depends(get_db),
) -> list[ClarificationOut]:
    """List pending clarification requests (optionally filtered by dossier)."""
    rows = await clarification_service.get_pending_clarifications(session, dossier_id=dossier_id)
    return [ClarificationOut.model_validate(r) for r in rows]


@router.post(
    "/clarifications/{clarification_id}/answer",
    response_model=ClarificationOut,
    status_code=status.HTTP_200_OK,
)
async def answer_clarification(
    clarification_id: int,
    body: ClarificationAnswer,
    session: AsyncSession = Depends(get_db),
) -> ClarificationOut:
    """Submit human answer and resume paused appraisal via Celery."""
    try:
        row = await clarification_service.submit_answer(
            session,
            clarification_id,
            body.answer_id,
            body.comment,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    resume_appraisal_task.delay(clarification_id)
    return ClarificationOut.model_validate(row)
