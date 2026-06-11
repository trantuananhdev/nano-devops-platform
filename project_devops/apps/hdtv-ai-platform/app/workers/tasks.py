"""
T-25: Celery tasks với absolute timeout guard.

run_appraisal_task: bọc run_appraisal() trong asyncio.wait_for(appraisal_max_duration_s)
  → nếu timeout → set dossier needs_revision + emit WS "timeout" event + increment metric.
"""
import asyncio
import logging

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.core.metrics import APPRAISAL_TIMEOUTS
from app.models.entities import Dossier, DossierStatus
from app.services.clarification_service import ClarificationPaused
from app.services.orchestrator.react_agent import resume_appraisal, run_appraisal
from app.services.pubsub import publish_event
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="run_appraisal_task", bind=True)
def run_appraisal_task(self, dossier_id: int, user_id: int | None = None) -> dict:
    """Run full appraisal with absolute timeout guard (T-25)."""
    task_id = self.request.id or "local-task"
    cfg = get_settings()

    async def _run() -> dict:
        async with async_session_factory() as session:
            try:
                result = await asyncio.wait_for(
                    run_appraisal(session, dossier_id, task_id, user_id=user_id),
                    timeout=float(cfg.appraisal_max_duration_s),
                )
                return {"appraisal_id": result.id, "overall_risk": result.overall_risk.value}

            except asyncio.TimeoutError:
                APPRAISAL_TIMEOUTS.inc()
                logger.error(
                    "Appraisal task timeout (%ds) for dossier_id=%d task_id=%s",
                    cfg.appraisal_max_duration_s, dossier_id, task_id,
                )
                # Best-effort: mark dossier as needs_revision
                try:
                    dossier = await session.get(Dossier, dossier_id)
                    if dossier:
                        dossier.status = DossierStatus.needs_revision
                        await session.commit()
                except Exception as db_exc:
                    logger.warning("Failed to update dossier status on timeout: %s", db_exc)

                # Emit WS timeout event (best-effort, non-blocking)
                try:
                    await publish_event(
                        dossier_id,
                        {
                            "type":    "timeout",
                            "task_id": task_id,
                            "reason":  f"Appraisal exceeded {cfg.appraisal_max_duration_s}s limit",
                        },
                    )
                except Exception:
                    pass

                return {
                    "status":     "timeout",
                    "dossier_id": dossier_id,
                    "reason":     f"Exceeded {cfg.appraisal_max_duration_s}s limit",
                }

            except ClarificationPaused as exc:
                return {
                    "status":            "awaiting_clarification",
                    "clarification_id":  exc.clarification_id,
                    "dossier_id":        dossier_id,
                }

            except Exception as exc:
                logger.exception("Appraisal task unexpected error for dossier_id=%d", dossier_id)
                return {"status": "error", "reason": str(exc), "dossier_id": dossier_id}

    return asyncio.run(_run())


@celery_app.task(name="resume_appraisal_task", bind=True)
def resume_appraisal_task(self, clarification_id: int) -> dict:
    """Resume a paused appraisal after HITL clarification answer (T-22)."""
    async def _run() -> dict:
        async with async_session_factory() as session:
            result = await resume_appraisal(session, clarification_id)
            return {"appraisal_id": result.id, "overall_risk": result.overall_risk.value}

    return asyncio.run(_run())
