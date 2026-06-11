"""Schemas for T-33: API Key Management."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ApiKeyCreate(BaseModel):
    """Body for POST /api-keys — submit the raw key once; it will be hashed."""

    name: str = Field(..., min_length=1, max_length=128, description="Human-readable label, e.g. 'Gemini prod key 1'")
    key_type: str = Field(..., description="One of: gemini, mcp, minio, internal")
    raw_key: str = Field(..., min_length=8, description="The actual API key — stored as bcrypt hash, never returned")


class ApiKeyOut(BaseModel):
    """Safe API key representation — hashed_key is NEVER included."""

    id: int
    name: str
    key_type: str
    key_prefix: str
    is_active: bool
    created_by: int | None
    last_used_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ApiKeyCreatedOut(ApiKeyOut):
    """Returned only on creation — includes masked preview (not the full key)."""

    # e.g. "AIzaSy********************XYZ" — first 8 + masked middle + last 4
    masked_key: str
