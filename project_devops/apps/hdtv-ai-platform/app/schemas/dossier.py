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


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: str
    tool_name: str
    execution_time_ms: int
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    created_at: datetime | None = None

