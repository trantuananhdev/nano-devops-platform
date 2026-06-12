from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.schemas.dossier import GeneralAuditLogOut, GeneralAuditLogPage
from app.services import audit_service
from app.models.entities import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["Audit Trail"])


@router.get("", response_model=GeneralAuditLogPage)
async def list_audit_logs(
    dossier_id: int | None = Query(None, ge=1, description="Filter by dossier ID"),
    user_id: int | None = Query(None, ge=1, description="Filter by user ID"),
    action: str | None = Query(None, description="Filter by action type"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(100, ge=1, le=500, description="Pagination limit"),
    session: AsyncSession = Depends(get_db),
) -> GeneralAuditLogPage:
    """Get paginated list of audit logs with optional filters."""
    items = await audit_service.get_audit_logs(
        session=session,
        dossier_id=dossier_id,
        user_id=user_id,
        action=action,
        limit=limit,
        offset=offset,
    )
    
    # Get total count
    count_query = select(func.count(AuditLog.id))
    if dossier_id:
        count_query = count_query.where(AuditLog.dossier_id == dossier_id)
    if user_id:
        count_query = count_query.where(AuditLog.user_id == user_id)
    if action:
        count_query = count_query.where(AuditLog.action == action)
    count_result = await session.execute(count_query)
    total = count_result.scalar() or 0
    
    return GeneralAuditLogPage(
        items=[GeneralAuditLogOut.model_validate(item) for item in items],
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + limit) < total,
    )


@router.get("/{audit_log_id}", response_model=GeneralAuditLogOut)
async def get_audit_log(
    audit_log_id: int,
    session: AsyncSession = Depends(get_db),
) -> GeneralAuditLogOut:
    """Get single audit log entry by ID."""
    from sqlalchemy.orm import selectinload
    result = await session.execute(
        select(AuditLog)
        .options(selectinload(AuditLog.user))
        .where(AuditLog.id == audit_log_id)
    )
    log = result.scalar_one_or_none()
    if not log:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Audit log not found")
    return GeneralAuditLogOut.model_validate(log)
