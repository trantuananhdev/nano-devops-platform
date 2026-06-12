from typing import Any

from pydantic import BaseModel


class ToolOut(BaseModel):
    name: str
    description: str
    category: str
    status: str
    usage_count: int = 0
    last_used_at: str | None = None


class GraphNodeOut(BaseModel):
    id: str
    type: str
    label: str
    desc: str
    x: float
    y: float


class GraphEdgeOut(BaseModel):
    source: str
    target: str
    label: str


class KnowledgeGraphOut(BaseModel):
    dossier_id: int
    dossier_title: str
    nodes: list[GraphNodeOut]
    edges: list[GraphEdgeOut]


class ChecklistItemOut(BaseModel):
    id: int
    text: str
    type: str
    is_required: bool


class SkillTemplateOut(BaseModel):
    id: int
    name: str
    description: str
    type: str = "prompt"
    is_active: bool
    markdown_content: str


class ScheduleJobOut(BaseModel):
    id: int
    name: str
    cron: str
    schedule_text: str
    tools: list[str]
    status: str
    description: str


class DashboardSummaryOut(BaseModel):
    pending_count: int
    high_risk_count: int
    approved_count: int
    open_alerts: int
    alert_sources: list[dict[str, Any]]
    notable_dossiers: list[dict[str, Any]]


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: str
    is_active: bool


class RoleOut(BaseModel):
    id: str
    name: str
    desc: str
    users_count: int


class SystemLogOut(BaseModel):
    id: int
    time: str
    user: str
    action: str
    details: str
    type: str


# T-16: User Preference schemas
class UserPreferenceOut(BaseModel):
    user_id: int
    key: str
    value: Any


class UserPreferenceUpdate(BaseModel):
    """PUT body: partial key-value map to upsert."""
    preferences: dict[str, Any]


class AgentMetricsOut(BaseModel):
    """T-24: Agent intelligence KPIs for admin dashboard."""

    plan_revision_rate: float
    critic_rejection_rate: float
    feedback_total: int
    memory_retrieval_count: int
    total_plans: int = 0
    revised_plans: int = 0
    total_appraisals: int = 0
    critic_rejections: int = 0
    feedback_approve: int = 0
    feedback_reject: int = 0
    feedback_adjust: int = 0
    memories_indexed: int = 0
    tool_calls_total: int = 0

