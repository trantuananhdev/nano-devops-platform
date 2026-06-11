from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FeedbackCreate(BaseModel):
    """T-20: User feedback on an appraisal result."""

    feedback_type: str = Field(
        ...,
        pattern="^(approve|reject|adjust)$",
        description="approve=👍, reject=👎, adjust=manual correction",
    )
    comment: str | None = Field(None, max_length=2000)
    user_id: int | None = Field(None, ge=1)
    appraisal_result_id: int | None = Field(None, ge=1)
    corrected_risk_level: str | None = Field(
        None, pattern="^(low|medium|high)$", description="Optional risk correction"
    )


class FeedbackOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dossier_id: int
    appraisal_result_id: int | None
    user_id: int | None
    feedback_type: str
    comment: str | None
    corrected_risk_level: str | None = None
    created_at: datetime | None = None

    @field_validator("corrected_risk_level", mode="before")
    @classmethod
    def _risk_to_str(cls, v: Any) -> str | None:
        if v is None:
            return None
        return v.value if hasattr(v, "value") else str(v)


class FeedbackStats(BaseModel):
    """Aggregate feedback counts for agent learning dashboard."""

    total: int
    approve: int
    reject: int
    adjust: int
    negative_lessons_indexed: int = Field(
        description="Reject/adjust feedback embedded in Chroma feedback_lessons"
    )
    degraded_chroma: bool = Field(
        default=False,
        description="True when last negative feedback could not reach Chroma",
    )
