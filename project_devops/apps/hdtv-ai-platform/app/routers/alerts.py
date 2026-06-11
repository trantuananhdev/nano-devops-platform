from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.dossier import AlertOut
from app.services.dossier_service import list_alerts, resolve_alert

router = APIRouter()


@router.get("", response_model=list[AlertOut])
async def get_alerts(
    status: str | None = None,
    session: AsyncSession = Depends(get_db),
) -> list[AlertOut]:
    alerts = await list_alerts(session, status=status)
    return [AlertOut.model_validate(a) for a in alerts]


@router.patch("/{alert_id}/resolve", response_model=AlertOut)
async def patch_resolve_alert(
    alert_id: int,
    session: AsyncSession = Depends(get_db),
) -> AlertOut:
    alert = await resolve_alert(session, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return AlertOut.model_validate(alert)
