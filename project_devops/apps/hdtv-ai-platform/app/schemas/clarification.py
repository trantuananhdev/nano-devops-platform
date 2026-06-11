"""T-22: Agent clarification request/response schemas."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ClarificationOption(BaseModel):
    id: str
    label: str


class ClarificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    dossier_id: int
    task_id: str
    question: str
    options: list[dict[str, Any]]
    status: str
    answer: str | None = None
    trigger_type: str | None = None
    created_at: datetime | None = None
    answered_at: datetime | None = None


class ClarificationAnswer(BaseModel):
    answer_id: str = Field(..., min_length=1, max_length=128)
    comment: str | None = Field(None, max_length=2000)
