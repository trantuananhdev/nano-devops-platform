from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.dossier import AuditLogOut
from app.services.dossier_service import list_audit_logs

router = APIRouter()


@router.get("", response_model=list[AuditLogOut])
async def get_audit_logs(
    limit: int = 50,
    session: AsyncSession = Depends(get_db),
) -> list[AuditLogOut]:
    logs = await list_audit_logs(session, limit=limit)
    return [AuditLogOut.model_validate(log) for log in logs]
