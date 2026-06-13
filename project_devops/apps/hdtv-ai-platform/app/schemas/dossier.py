from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class HealthOut(BaseModel):
    status: str = "ok"
    service: str = "hdtv-ai-platform"


class DossierCreate(BaseModel):
    """T-13: Input schema for creating a new dossier via POST /dossiers."""

    doc_no: str = Field(..., min_length=2, max_length=64, description="Ký hiệu Tờ trình, e.g. 124/TTr-B02")
    title: str = Field(..., min_length=5, max_length=1000, description="Trích yếu nội dung Tờ trình")
    unit: str = Field(..., min_length=2, max_length=255, description="Tên Ban/Đơn vị trình")


class DossierOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doc_no: str
    title: str
    unit: str
    risk_level: str
    status: str
    created_at: datetime | None = None


class AppraisalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    overall_risk: str
    report_md: str
    resolution_md: str
    checks: dict[str, Any]
    created_at: datetime | None = None


class DossierDetail(DossierOut):
    pdf_url: str | None = None
    appraisal: AppraisalOut | None = None


class AppraiseRequest(BaseModel):
    """T-23: Optional body payload for personalized appraisal."""

    user_id: int | None = Field(None, ge=1, description="User ID for role-based agent profile")


class AppraiseResponse(BaseModel):
    task_id: str
    dossier_id: int
    status: str = "queued"


class PdfUrlOut(BaseModel):
    """T-14: Presigned GET URL for viewing uploaded PDF."""

    dossier_id: int
    pdf_url: str
    expires_in: int = 3600


class UploadResult(BaseModel):
    """T-13: Response after PDF upload."""

    dossier_id: int
    pdf_key: str
    pdf_url: str
    ok: bool
    error: str | None = None


class DossierPage(BaseModel):
    """T-40: Paginated dossier list response."""

    items: list[DossierOut]
    total: int
    offset: int
    limit: int
    has_more: bool


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dossier_id: int | None
    severity: str
    source: str
    description: str
    status: str
    created_at: datetime | None = None


class StatusTransitionRequest(BaseModel):
    """Request to transition dossier to new status."""
    new_status: str
    changed_by: int | None = None
    comment: str | None = None


class StatusHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dossier_id: int
    from_status: str | None
    to_status: str
    changed_by: int | None
    comment: str | None
    created_at: datetime


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    tool_name: str
    execution_time_ms: int
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    created_at: datetime | None = None


from app.schemas.meta import UserOut

class GeneralAuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dossier_id: int | None
    user_id: int | None
    user: UserOut | None = None
    action: str
    description: str | None
    extra_data: dict[str, Any]
    ip_address: str | None
    created_at: datetime


class GeneralAuditLogPage(BaseModel):
    items: list[GeneralAuditLogOut]
    total: int
    offset: int
    limit: int
    has_more: bool


class ReferenceDocumentCreate(BaseModel):
    file_name: str
    file_key: str
    file_size: int | None = None
    content_type: str | None = None


class ReferenceDocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    dossier_id: int
    file_name: str
    file_key: str
    file_size: int | None
    content_type: str | None
    uploaded_by: int | None
    uploaded_at: datetime


class DocumentVersionCreate(BaseModel):
    content: str | None
    content_type: str | None
    change_description: str | None


class DocumentVersionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    dossier_id: int
    version_number: int
    content: str | None
    content_type: str | None
    change_description: str | None
    created_by: int | None
    created_at: datetime


class NotificationCreate(BaseModel):
    user_id: int
    dossier_id: int | None = None
    type: str
    title: str
    message: str
    extra_data: dict[str, Any] = Field(default_factory=dict)


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    user_id: int
    dossier_id: int | None
    type: str
    title: str
    message: str
    is_read: bool
    extra_data: dict[str, Any]
    created_at: datetime


class NotificationMarkRead(BaseModel):
    is_read: bool = True


class NotificationPage(BaseModel):
    items: list[NotificationOut]
    total: int
    offset: int
    limit: int
    has_more: bool
    unread_count: int

