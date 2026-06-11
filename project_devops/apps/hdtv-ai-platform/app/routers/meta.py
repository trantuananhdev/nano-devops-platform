from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.meta import (
    AgentMetricsOut,
    ChecklistItemOut,
    DashboardSummaryOut,
    KnowledgeGraphOut,
    RoleOut,
    ScheduleJobOut,
    SkillTemplateOut,
    SystemLogOut,
    ToolOut,
    UserOut,
    UserPreferenceOut,
    UserPreferenceUpdate,
)
from app.services import agent_metrics_service, meta_service
from app.services.memory import preference_service
from app.services.llm_router import get_model_registry

router = APIRouter()


@router.get("/tools", response_model=list[ToolOut])
async def get_tools(session: AsyncSession = Depends(get_db)) -> list[ToolOut]:
    return await meta_service.list_tool_registry(session)


@router.get("/knowledge-graph", response_model=KnowledgeGraphOut)
async def get_knowledge_graph(
    dossier_id: int = Query(..., ge=1),
    session: AsyncSession = Depends(get_db),
) -> KnowledgeGraphOut:
    graph = await meta_service.build_knowledge_graph(session, dossier_id)
    if not graph:
        raise HTTPException(status_code=404, detail="Dossier not found")
    return graph


@router.get("/dashboard/summary", response_model=DashboardSummaryOut)
async def get_dashboard_summary(
    session: AsyncSession = Depends(get_db),
) -> DashboardSummaryOut:
    return await meta_service.dashboard_summary(session)


@router.get("/schedules", response_model=list[ScheduleJobOut])
async def get_schedules() -> list[ScheduleJobOut]:
    return meta_service.list_schedule_jobs()


@router.get("/skills", response_model=list[SkillTemplateOut])
async def get_skills() -> list[SkillTemplateOut]:
    return meta_service.list_skill_templates()


@router.get("/checklist-template", response_model=list[ChecklistItemOut])
async def get_checklist_template() -> list[ChecklistItemOut]:
    return meta_service.default_checklist()


# T-14: Admin panel endpoints
@router.get("/users", response_model=list[UserOut])
async def get_users() -> list[UserOut]:
    return meta_service.list_users()


@router.get("/roles", response_model=list[RoleOut])
async def get_roles() -> list[RoleOut]:
    return meta_service.list_roles()


@router.get("/system-logs", response_model=list[SystemLogOut])
async def get_system_logs() -> list[SystemLogOut]:
    return meta_service.list_system_logs()


# T-16: User preference endpoints
@router.get("/users/{user_id}/preferences", response_model=list[UserPreferenceOut])
async def get_user_preferences(
    user_id: int,
    session: AsyncSession = Depends(get_db),
) -> list[UserPreferenceOut]:
    """Return all preferences for a user. Returns empty list if none set."""
    prefs = await preference_service.get_preferences(session, user_id)
    return [
        UserPreferenceOut(user_id=user_id, key=k, value=v)
        for k, v in prefs.items()
    ]


@router.put("/users/{user_id}/preferences", response_model=list[UserPreferenceOut])
async def update_user_preferences(
    user_id: int,
    body: UserPreferenceUpdate,
    session: AsyncSession = Depends(get_db),
) -> list[UserPreferenceOut]:
    """Upsert one or more preferences for a user."""
    await preference_service.set_preferences_bulk(session, user_id, body.preferences)
    prefs = await preference_service.get_preferences(session, user_id)
    return [
        UserPreferenceOut(user_id=user_id, key=k, value=v)
        for k, v in prefs.items()
    ]


# T-24: Agent intelligence metrics
@router.get("/agent/metrics", response_model=AgentMetricsOut)
async def get_agent_metrics(
    session: AsyncSession = Depends(get_db),
) -> AgentMetricsOut:
    """Aggregate plan revision, critic rejection, feedback, and memory KPIs."""
    data = await agent_metrics_service.get_agent_metrics(session)
    return AgentMetricsOut(**data)


@router.get("/agent/models")
async def get_agent_models() -> list[dict]:
    """Return the multi-model registry — which AI model handles which agent role.

    Used by the FE dashboard to display the 'AI Models' panel showing
    Gemma-4 vs Gemini-Flash assignments per role.
    """
    return get_model_registry()
