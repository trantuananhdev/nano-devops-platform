import asyncio
import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select

from app.core.database import async_session_factory
from app.models.entities import AppraisalResult, Dossier
from app.services.pubsub import subscribe_events

router = APIRouter()
logger = logging.getLogger(__name__)


async def _get_dossier_snapshot(dossier_id: int) -> dict | None:
    """Return current dossier state for initial WS snapshot.

    Sent immediately on connect so the client gets the latest status even if
    the appraisal completed while the WebSocket was disconnected.
    """
    try:
        async with async_session_factory() as session:
            dossier = await session.get(Dossier, dossier_id)
            if not dossier:
                return None
            # Fetch most recent appraisal result if any
            result = await session.execute(
                select(AppraisalResult)
                .where(AppraisalResult.dossier_id == dossier_id)
                .order_by(AppraisalResult.id.desc())
                .limit(1)
            )
            appraisal = result.scalar_one_or_none()
            snapshot: dict = {
                "type":       "snapshot",
                "dossier_id": dossier_id,
                "status":     dossier.status.value,
                "risk_level": dossier.risk_level.value,
            }
            if appraisal:
                snapshot["appraisal_id"]  = appraisal.id
                snapshot["overall_risk"]  = appraisal.overall_risk.value
                # If already completed, send a synthetic "completed" so FE
                # can render result without waiting for a new event.
                if dossier.status.value in ("approved", "needs_revision"):
                    snapshot["completed"] = True
            return snapshot
    except Exception as exc:
        logger.warning("WS snapshot failed for dossier %d: %s", dossier_id, exc)
        return None


@router.websocket("/ws/appraisal/{dossier_id}")
async def appraisal_ws(websocket: WebSocket, dossier_id: int) -> None:
    await websocket.accept()
    client, pubsub = await subscribe_events(dossier_id)
    try:
        # Send current dossier state immediately on connect.
        # This ensures the client sees the latest status even after a
        # reconnect that missed events during the disconnect window.
        snapshot = await _get_dossier_snapshot(dossier_id)
        if snapshot:
            await websocket.send_text(json.dumps(snapshot, ensure_ascii=False))

        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message and message.get("type") == "message":
                await websocket.send_text(message["data"])
            await asyncio.sleep(0.05)
    except WebSocketDisconnect:
        pass
    finally:
        await pubsub.unsubscribe()
        await pubsub.close()
        await client.aclose()
