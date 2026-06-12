from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.entities import Dossier, DossierStatus, UserRole, StatusHistory
from app.core.permissions import is_allowed_to_submit_to_dept, is_allowed_to_approve_dept, is_allowed_to_submit_to_board, is_allowed_to_approve_final
from app.services.audit_service import log_audit_event


# Define valid status transitions
VALID_TRANSITIONS = {
    DossierStatus.draft: [DossierStatus.pending, DossierStatus.submitted_to_dept],
    DossierStatus.pending: [DossierStatus.appraising, DossierStatus.submitted_to_dept, DossierStatus.draft],
    DossierStatus.appraising: [DossierStatus.pending, DossierStatus.submitted_to_dept, DossierStatus.needs_revision, DossierStatus.approved],
    DossierStatus.submitted_to_dept: [DossierStatus.dept_approved, DossierStatus.dept_rejected, DossierStatus.draft],
    DossierStatus.dept_approved: [DossierStatus.submitted_to_board, DossierStatus.draft],
    DossierStatus.dept_rejected: [DossierStatus.draft],
    DossierStatus.submitted_to_board: [DossierStatus.board_reviewed, DossierStatus.dept_approved],
    DossierStatus.board_reviewed: [DossierStatus.approved, DossierStatus.rejected, DossierStatus.needs_revision],
    DossierStatus.approved: [],
    DossierStatus.rejected: [DossierStatus.draft],
    DossierStatus.needs_revision: [DossierStatus.draft],
}


async def transition_dossier_status(
    session: AsyncSession,
    dossier_id: int,
    new_status: DossierStatus,
    user_role: UserRole,
    changed_by: int | None = None,
    comment: str | None = None,
) -> Dossier:
    # Get dossier
    result = await session.execute(select(Dossier).where(Dossier.id == dossier_id))
    dossier = result.scalar_one_or_none()
    if not dossier:
        raise ValueError(f"Dossier with id {dossier_id} not found")

    # Check if transition is valid
    if new_status not in VALID_TRANSITIONS.get(dossier.status, []):
        raise ValueError(f"Invalid status transition from {dossier.status} to {new_status}")

    # Check permissions
    if new_status == DossierStatus.submitted_to_dept:
        if not is_allowed_to_submit_to_dept(user_role):
            raise PermissionError("You don't have permission to submit to department")
    elif new_status in [DossierStatus.dept_approved, DossierStatus.dept_rejected]:
        if not is_allowed_to_approve_dept(user_role):
            raise PermissionError("You don't have permission to approve/reject at department")
    elif new_status == DossierStatus.submitted_to_board:
        if not is_allowed_to_submit_to_board(user_role):
            raise PermissionError("You don't have permission to submit to board")
    elif new_status in [DossierStatus.approved, DossierStatus.rejected]:
        if not is_allowed_to_approve_final(user_role):
            raise PermissionError("You don't have permission to give final approval/rejection")

    # Create status history
    history_entry = StatusHistory(
        dossier_id=dossier_id,
        from_status=dossier.status,
        to_status=new_status,
        changed_by=changed_by,
        comment=comment,
    )
    session.add(history_entry)

    # Update dossier status
    old_status = dossier.status
    dossier.status = new_status

    # Commit status change and history first
    await session.commit()
    await session.refresh(dossier)
    
    # Log audit event
    await log_audit_event(
        session=session,
        action="status_transition",
        dossier_id=dossier_id,
        user_id=changed_by,
        description=f"Status changed from {old_status} to {new_status}",
        metadata={"old_status": old_status, "new_status": new_status, "comment": comment},
    )
    
    return dossier


async def get_dossier_status_history(session: AsyncSession, dossier_id: int) -> list[StatusHistory]:
    result = await session.execute(
        select(StatusHistory)
        .where(StatusHistory.dossier_id == dossier_id)
        .order_by(StatusHistory.created_at.desc())
    )
    return list(result.scalars().all())
