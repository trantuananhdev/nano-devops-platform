from typing import Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.entities import AuditLog, User


async def log_audit_event(
    session: AsyncSession,
    action: str,
    dossier_id: int | None = None,
    user_id: int | None = None,
    description: str | None = None,
    metadata: dict[str, Any] | None = None,
    ip_address: str | None = None,
) -> AuditLog:
    """Create and persist a new audit log entry."""
    audit_entry = AuditLog(
        action=action,
        dossier_id=dossier_id,
        user_id=user_id,
        description=description,
        metadata=metadata or {},
        ip_address=ip_address,
    )
    session.add(audit_entry)
    await session.commit()
    await session.refresh(audit_entry)
    return audit_entry


async def get_audit_logs(
    session: AsyncSession,
    dossier_id: int | None = None,
    user_id: int | None = None,
    action: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[AuditLog]:
    """Get audit logs with optional filters."""
    query = select(AuditLog).options(selectinload(AuditLog.user))
    
    if dossier_id:
        query = query.where(AuditLog.dossier_id == dossier_id)
    if user_id:
        query = query.where(AuditLog.user_id == user_id)
    if action:
        query = query.where(AuditLog.action == action)
        
    query = query.order_by(AuditLog.created_at.desc()).limit(limit).offset(offset)
    result = await session.execute(query)
    return list(result.scalars().all())
