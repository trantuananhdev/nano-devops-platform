from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.entities import (
    AgentPlan,
    AiAuditLog,
    Alert,
    AlertStatus,
    AppraisalResult,
    Dossier,
    DossierStatus,
    RiskLevel,
)
from app.schemas.dossier import AppraisalOut, AppraisalSummary, DossierCreate, DossierDetail, DossierOut


async def list_dossiers(
    session: AsyncSession,
    offset: int = 0,
    limit: int = 50,
    unit: str | None = None,
    risk_level: str | None = None,
) -> list[DossierOut]:
    """T-40: Return a paginated slice of dossiers ordered by id desc.

    offset — number of rows to skip (cursor-style pagination)
    limit  — max rows to return (capped at 200 to prevent accidental full-dumps)
    """
    limit = min(limit, 200)
    q = select(Dossier).order_by(Dossier.id.desc())
    if unit:
        q = q.where(Dossier.unit == unit)
    if risk_level:
        try:
            q = q.where(Dossier.risk_level == RiskLevel(risk_level))
        except ValueError:
            q = q.where(Dossier.risk_level == None)
    result = await session.execute(q.offset(offset).limit(limit))
    return [DossierOut.model_validate(d) for d in result.scalars().all()]


async def count_dossiers(
    session: AsyncSession,
    unit: str | None = None,
    risk_level: str | None = None,
) -> int:
    """T-40: Total count for pagination metadata."""
    q = select(func.count()).select_from(Dossier)
    if unit:
        q = q.where(Dossier.unit == unit)
    if risk_level:
        try:
            q = q.where(Dossier.risk_level == RiskLevel(risk_level))
        except ValueError:
            q = q.where(Dossier.risk_level == None)
    result = await session.execute(q)
    return result.scalar_one()


async def get_dossier_detail(session: AsyncSession, dossier_id: int) -> DossierDetail | None:
    result = await session.execute(
        select(Dossier)
        .where(Dossier.id == dossier_id)
        .options(selectinload(Dossier.appraisals))
    )
    dossier = result.scalar_one_or_none()
    if not dossier:
        return None
    appraisal = None
    if dossier.appraisals:
        latest = sorted(dossier.appraisals, key=lambda a: a.created_at or 0, reverse=True)[0]
        appraisal = AppraisalOut.model_validate(latest)

    plan_result = await session.execute(
        select(AgentPlan)
        .where(AgentPlan.dossier_id == dossier_id)
        .order_by(AgentPlan.id.desc())
        .limit(1)
    )
    latest_plan = plan_result.scalar_one_or_none()
    latest_appraisal = None
    if latest_plan and latest_plan.plan_json:
        steps = latest_plan.plan_json.get("steps", [])
        plan_steps = []
        for step in steps:
            plan_steps.append({
                "tool": step.get("tool"),
                "status": "pass",
                "desc": "Chờ thẩm định AI...",
                "label": step.get("tool"),
            })
        latest_appraisal = AppraisalSummary(plan_steps=plan_steps)

    return DossierDetail(
        **DossierOut.model_validate(dossier).model_dump(),
        pdf_url=dossier.pdf_url,
        appraisal=appraisal,
        latest_appraisal=latest_appraisal,
    )


async def create_dossier(session: AsyncSession, body: DossierCreate) -> Dossier:
    """T-13: Create a new dossier with default pending/low state.

    Raises ValueError if doc_no already exists (unique constraint).
    """
    existing = await session.execute(
        select(Dossier).where(Dossier.doc_no == body.doc_no)
    )
    if existing.scalar_one_or_none():
        raise ValueError(f"doc_no '{body.doc_no}' đã tồn tại")

    dossier = Dossier(
        doc_no=body.doc_no,
        title=body.title,
        unit=body.unit,
        risk_level=RiskLevel.low,
        status=DossierStatus.pending,
    )
    session.add(dossier)
    await session.commit()
    await session.refresh(dossier)
    return dossier


async def update_pdf_url(session: AsyncSession, dossier_id: int, pdf_url: str) -> Dossier | None:
    """T-13: Set pdf_url on dossier after MinIO upload."""
    dossier = await session.get(Dossier, dossier_id)
    if not dossier:
        return None
    dossier.pdf_url = pdf_url
    await session.commit()
    await session.refresh(dossier)
    return dossier


async def list_alerts(session: AsyncSession, status: str | None = None) -> list[Alert]:
    q = select(Alert).order_by(Alert.id.desc())
    if status:
        q = q.where(Alert.status == AlertStatus(status))
    result = await session.execute(q)
    return list(result.scalars().all())


async def resolve_alert(session: AsyncSession, alert_id: int) -> Alert | None:
    alert = await session.get(Alert, alert_id)
    if not alert:
        return None
    alert.status = AlertStatus.resolved
    await session.commit()
    await session.refresh(alert)
    return alert


async def list_audit_logs(session: AsyncSession, limit: int = 50) -> list[AiAuditLog]:
    result = await session.execute(
        select(AiAuditLog).order_by(AiAuditLog.id.desc()).limit(limit)
    )
    return list(result.scalars().all())

