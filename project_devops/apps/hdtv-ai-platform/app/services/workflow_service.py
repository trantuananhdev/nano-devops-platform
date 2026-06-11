"""T-12: BPMN workflow persistence service.

Router → Service → Repository pattern.
Audit log: every Save recorded in ai_audit_logs with tool_name='WorkflowSave'.
"""

import time
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AiAuditLog, Dossier, WorkflowDiagram


async def get_workflow(session: AsyncSession, dossier_id: int) -> WorkflowDiagram | None:
    """Return saved BPMN for given dossier, or None if not yet saved."""
    result = await session.execute(
        select(WorkflowDiagram).where(WorkflowDiagram.dossier_id == dossier_id)
    )
    return result.scalar_one_or_none()


async def save_workflow(
    session: AsyncSession,
    dossier_id: int,
    bpmn_xml: str,
) -> WorkflowDiagram:
    """Upsert BPMN XML for a dossier.

    Records action to ai_audit_logs — satisfies the 'every tool call → audit' rule
    (WorkflowSave is treated as a system tool invocation).
    """
    t0 = time.monotonic()

    # Validate dossier exists
    dossier = await session.get(Dossier, dossier_id)
    if not dossier:
        raise ValueError(f"Dossier {dossier_id} not found")

    # Upsert
    existing = await get_workflow(session, dossier_id)
    if existing:
        existing.bpmn_xml = bpmn_xml
        diagram = existing
    else:
        diagram = WorkflowDiagram(dossier_id=dossier_id, bpmn_xml=bpmn_xml)
        session.add(diagram)

    # Audit log
    duration_ms = int((time.monotonic() - t0) * 1000)
    session.add(
        AiAuditLog(
            task_id=str(uuid.uuid4()),
            tool_name="WorkflowSave",
            execution_time_ms=duration_ms,
            inputs={"dossier_id": dossier_id, "xml_length": len(bpmn_xml)},
            outputs={"action": "upsert", "dossier_doc_no": dossier.doc_no},
        )
    )

    await session.commit()
    await session.refresh(diagram)
    return diagram


async def list_workflows(session: AsyncSession) -> list[dict[str, Any]]:
    """Return all saved workflow metadata (no XML in list view — too large)."""
    rows = await session.execute(
        select(
            WorkflowDiagram.id,
            WorkflowDiagram.dossier_id,
            WorkflowDiagram.updated_at,
            Dossier.doc_no,
            Dossier.title,
        ).join(Dossier, Dossier.id == WorkflowDiagram.dossier_id)
    )
    return [
        {
            "id": row.id,
            "dossier_id": row.dossier_id,
            "doc_no": row.doc_no,
            "title": row.title,
            "updated_at": row.updated_at.isoformat() if row.updated_at else None,
        }
        for row in rows.all()
    ]
