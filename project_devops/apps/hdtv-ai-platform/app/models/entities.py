import enum
from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    hdtv_leader = "hdtv_leader"
    dept_head = "dept_head"
    specialist = "specialist"


class DossierStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    appraising = "appraising"
    submitted_to_dept = "submitted_to_dept"
    dept_approved = "dept_approved"
    dept_rejected = "dept_rejected"
    submitted_to_board = "submitted_to_board"
    board_reviewed = "board_reviewed"
    approved = "approved"
    rejected = "rejected"
    needs_revision = "needs_revision"


class RiskLevel(str, enum.Enum):
    high = "high"
    medium = "medium"
    low = "low"


class AlertStatus(str, enum.Enum):
    open = "open"
    resolved = "resolved"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.specialist)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class StatusHistory(Base):
    __tablename__ = "status_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dossier_id: Mapped[int] = mapped_column(ForeignKey("dossiers.id"), nullable=False, index=True)
    from_status: Mapped[DossierStatus | None] = mapped_column(Enum(DossierStatus), nullable=True)
    to_status: Mapped[DossierStatus] = mapped_column(Enum(DossierStatus), nullable=False)
    changed_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Dossier(Base):
    __tablename__ = "dossiers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    doc_no: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    unit: Mapped[str] = mapped_column(String(255), nullable=False)
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), default=RiskLevel.low)
    status: Mapped[DossierStatus] = mapped_column(Enum(DossierStatus), default=DossierStatus.draft)
    pdf_url: Mapped[str | None] = mapped_column(String(512))
    pdf_text: Mapped[str | None] = mapped_column(Text)  # OCR extracted text
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    appraisals: Mapped[list["AppraisalResult"]] = relationship(back_populates="dossier")
    alerts: Mapped[list["Alert"]] = relationship(back_populates="dossier")
    workflows: Mapped[list["WorkflowDiagram"]] = relationship(back_populates="dossier")
    agent_memories: Mapped[list["AgentMemory"]] = relationship(back_populates="dossier")
    feedbacks: Mapped[list["AgentFeedback"]] = relationship(back_populates="dossier")
    status_history: Mapped[list["StatusHistory"]] = relationship("StatusHistory", order_by="StatusHistory.created_at.desc()")


class AppraisalResult(Base):
    __tablename__ = "appraisal_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dossier_id: Mapped[int] = mapped_column(ForeignKey("dossiers.id"), nullable=False)
    overall_risk: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False)
    report_md: Mapped[str] = mapped_column(Text, default="")
    resolution_md: Mapped[str] = mapped_column(Text, default="")
    checks: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    critic_verdict: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dossier: Mapped["Dossier"] = relationship(back_populates="appraisals")


class Alert(Base):
    __tablename__ = "alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dossier_id: Mapped[int | None] = mapped_column(ForeignKey("dossiers.id"))
    severity: Mapped[str] = mapped_column(String(32), nullable=False)
    source: Mapped[str] = mapped_column(String(128), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AlertStatus] = mapped_column(Enum(AlertStatus), default=AlertStatus.open)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dossier: Mapped["Dossier | None"] = relationship(back_populates="alerts")


class AiAuditLog(Base):
    __tablename__ = "ai_audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False)
    execution_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    outputs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # T-30: Audit correlation — links log row back to the specific plan step that triggered it
    plan_step_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    # T-30: Error taxonomy — transient | bad_input | unavailable | unknown | None (success)
    error_type: Mapped[str | None] = mapped_column(String(32), nullable=True)


class WorkflowDiagram(Base):
    """Persists BPMN XML diagrams per dossier (T-12: BPMN workflow persistence)."""

    __tablename__ = "workflow_diagrams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dossier_id: Mapped[int] = mapped_column(ForeignKey("dossiers.id"), nullable=False, index=True)
    bpmn_xml: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    dossier: Mapped["Dossier"] = relationship(back_populates="workflows")


class ToolConfig(Base):
    """Dynamic tool configuration stored in database."""

    __tablename__ = "tool_configs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(String(64), nullable=False)  # legal, financial, project, etc.
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    config_schema: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # Input schema for the tool
    fallback_response: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    output_mapping: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)  # T-21: source output → target input fields
    chains_to: Mapped[list[Any]] = mapped_column(JSONB, default=list)  # T-21: tool names to auto-run after this tool
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class AgentMemory(Base):
    """Memory of agent's thoughts, observations, and actions for each dossier."""

    __tablename__ = "agent_memories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dossier_id: Mapped[int] = mapped_column(ForeignKey("dossiers.id"), nullable=False, index=True)
    step: Mapped[int] = mapped_column(Integer, nullable=False)
    thought: Mapped[str] = mapped_column(Text, nullable=False)
    action: Mapped[str] = mapped_column(String(64), nullable=False)  # tool_call, finish
    tool_name: Mapped[str | None] = mapped_column(String(128))
    tool_input: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    observation: Mapped[str | None] = mapped_column(Text)
    embedding_id: Mapped[str | None] = mapped_column(String(128))  # T-15: Chroma doc id after upsert
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dossier: Mapped["Dossier"] = relationship(back_populates="agent_memories")


class AgentFeedback(Base):
    """Feedback from users on agent's decisions for continuous learning."""

    __tablename__ = "agent_feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dossier_id: Mapped[int] = mapped_column(ForeignKey("dossiers.id"), nullable=False, index=True)
    appraisal_result_id: Mapped[int | None] = mapped_column(ForeignKey("appraisal_results.id"))
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    feedback_type: Mapped[str] = mapped_column(String(64), nullable=False)  # approve, reject, adjust
    comment: Mapped[str | None] = mapped_column(Text)
    corrected_risk_level: Mapped[RiskLevel | None] = mapped_column(Enum(RiskLevel))
    feedback_meta: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    dossier: Mapped["Dossier"] = relationship(back_populates="feedbacks")


class RiskRule(Base):
    """Configurable risk rules stored in database."""

    __tablename__ = "risk_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    condition_expression: Mapped[str] = mapped_column(Text, nullable=False)  # Python expression
    risk_level: Mapped[RiskLevel] = mapped_column(Enum(RiskLevel), nullable=False)
    priority: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentPlanStatus(str, enum.Enum):
    pending = "pending"
    executing = "executing"
    completed = "completed"
    revised = "revised"
    failed = "failed"


class AgentPlan(Base):
    """Persisted LLM execution plan per appraisal (T-17: plan-execute-reflect)."""

    __tablename__ = "agent_plans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dossier_id: Mapped[int] = mapped_column(ForeignKey("dossiers.id"), nullable=False, index=True)
    plan_json: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    revision: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(32), default=AgentPlanStatus.pending.value)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ClarificationStatus(str, enum.Enum):
    pending = "pending"
    answered = "answered"


class AgentClarification(Base):
    """Human-in-the-loop clarification pause/resume (T-22)."""

    __tablename__ = "agent_clarifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dossier_id: Mapped[int] = mapped_column(ForeignKey("dossiers.id"), nullable=False, index=True)
    task_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    status: Mapped[str] = mapped_column(String(32), default=ClarificationStatus.pending.value)
    answer: Mapped[str | None] = mapped_column(String(512))
    trigger_type: Mapped[str | None] = mapped_column(String(64))
    resume_state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    answered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class UserPreference(Base):
    """Per-user preference key-value store (T-16: cross-dossier memory + personalization)."""

    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    key: Mapped[str] = mapped_column(String(128), nullable=False)
    value: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


# ---------------------------------------------------------------------------
# T-33: API Keys Management — secure key storage with hashing
# ---------------------------------------------------------------------------

class ApiKeyType(str, enum.Enum):
    gemini = "gemini"
    mcp = "mcp"
    minio = "minio"
    internal = "internal"


class ApiKey(Base):
    """Secure storage for API keys.

    Keys are hashed with bcrypt before persistence.
    The raw key is only visible once at creation time.

    key_prefix stores the first 8 chars for display/identification.
    """

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    key_type: Mapped[ApiKeyType] = mapped_column(Enum(ApiKeyType), nullable=False, index=True)
    # First 8 chars of raw key — safe to store/display, used for identification
    key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)
    # bcrypt-hashed key value — never store plaintext
    hashed_key: Mapped[str] = mapped_column(String(255), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


# ---------------------------------------------------------------------------
# T-36: MCP Call Log — audit trail for every MCP API call
# ---------------------------------------------------------------------------

class McpCallLog(Base):
    """Per-call audit log for MCP tool invocations (T-36).

    Separate from AiAuditLog to enable dedicated MCP audit views without
    polluting the main AI audit feed.
    """

    __tablename__ = "mcp_call_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # MCP client identity — determined by API key used
    api_key_id: Mapped[int | None] = mapped_column(ForeignKey("api_keys.id"), nullable=True, index=True)
    api_key_prefix: Mapped[str] = mapped_column(String(16), nullable=False)  # denormalized for fast display
    # MCP call details
    tool_name: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    inputs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    outputs: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_error: Mapped[bool] = mapped_column(Boolean, default=False)
    is_streaming: Mapped[bool] = mapped_column(Boolean, default=False)  # True = SSE stream call
    execution_ms: Mapped[int] = mapped_column(Integer, default=0)
    # Validation outcome (T-29 output schema)
    output_incomplete: Mapped[bool] = mapped_column(Boolean, default=False)
    missing_fields: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class AuditLog(Base):
    """General audit log for all important actions (T-49: Audit Trail)."""

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dossier_id: Mapped[int | None] = mapped_column(ForeignKey("dossiers.id"), nullable=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128), nullable=False, index=True)  # e.g., "create_dossier", "status_change", "upload_pdf"
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)

