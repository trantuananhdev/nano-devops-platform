"""T-12: BPMN workflow persistence router.

Endpoints:
  GET  /api/v1/workflows               — list all saved diagrams (metadata only)
  GET  /api/v1/workflows/{dossier_id}  — get BPMN XML for a dossier
  PUT  /api/v1/workflows/{dossier_id}  — upsert BPMN XML (Save button)
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services import workflow_service

router = APIRouter()


class WorkflowIn(BaseModel):
    bpmn_xml: str = Field(..., min_length=10, description="Full BPMN 2.0 XML string")


class WorkflowOut(BaseModel):
    id: int
    dossier_id: int
    bpmn_xml: str
    updated_at: str | None = None

    model_config = {"from_attributes": True}


class WorkflowMetaOut(BaseModel):
    id: int
    dossier_id: int
    doc_no: str
    title: str
    updated_at: str | None = None


@router.get("/workflows", response_model=list[WorkflowMetaOut], summary="List saved BPMN diagrams")
async def list_workflows(session: AsyncSession = Depends(get_db)) -> list[Any]:
    return await workflow_service.list_workflows(session)


@router.get(
    "/workflows/{dossier_id}",
    response_model=WorkflowOut,
    summary="Get BPMN diagram for a dossier",
)
async def get_workflow(
    dossier_id: int,
    session: AsyncSession = Depends(get_db),
) -> WorkflowOut:
    diagram = await workflow_service.get_workflow(session, dossier_id)
    if not diagram:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No saved workflow for this dossier")
    return WorkflowOut(
        id=diagram.id,
        dossier_id=diagram.dossier_id,
        bpmn_xml=diagram.bpmn_xml,
        updated_at=diagram.updated_at.isoformat() if diagram.updated_at else None,
    )


@router.put(
    "/workflows/{dossier_id}",
    response_model=WorkflowOut,
    summary="Save (upsert) BPMN diagram for a dossier",
)
async def save_workflow(
    dossier_id: int,
    body: WorkflowIn,
    session: AsyncSession = Depends(get_db),
) -> WorkflowOut:
    try:
        diagram = await workflow_service.save_workflow(session, dossier_id, body.bpmn_xml)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return WorkflowOut(
        id=diagram.id,
        dossier_id=diagram.dossier_id,
        bpmn_xml=diagram.bpmn_xml,
        updated_at=diagram.updated_at.isoformat() if diagram.updated_at else None,
    )
