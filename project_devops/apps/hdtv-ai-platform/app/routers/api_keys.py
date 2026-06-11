"""
Router: /api/v1/api-keys — T-33: API Key Management endpoints.

Endpoints:
  GET    /api-keys               List all keys (metadata only, no raw/hash)
  GET    /api-keys?key_type=gemini  Filter by type
  POST   /api-keys               Create + hash a new key (returns masked preview once)
  DELETE /api-keys/{id}          Deactivate a key (soft-delete)

Security:
  - hashed_key is never returned in any response.
  - The raw key is only visible in the POST response (masked_key field).
  - Gemini keys use reversible base64 (needed by llm_router for retrieval).
  - MCP/internal keys use bcrypt (server-side verify only).
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreatedOut, ApiKeyOut
from app.services.api_key_service import create_api_key, delete_api_key, encode_gemini_key, list_api_keys

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api-keys", tags=["api-keys"])


@router.get("", response_model=list[ApiKeyOut])
async def get_api_keys(
    key_type: str | None = Query(default=None, description="Filter by type: gemini|mcp|minio|internal"),
    db: AsyncSession = Depends(get_db),
) -> list[ApiKeyOut]:
    """List API keys — metadata only. hashed_key is never included."""
    return await list_api_keys(db, key_type=key_type)


@router.post("", response_model=ApiKeyCreatedOut, status_code=status.HTTP_201_CREATED)
async def add_api_key(
    body: ApiKeyCreate,
    db: AsyncSession = Depends(get_db),
) -> ApiKeyCreatedOut:
    """Add a new API key.

    The raw_key is hashed before persistence.
    For gemini type, a reversible encoding is used so llm_router can retrieve it.
    The response includes masked_key (first 8 + *** + last 4) — only visible once.
    """
    # For Gemini keys: use reversible encoding so llm_router can get them back.
    # For other types: use proper bcrypt (verified server-side only).
    original_raw = body.raw_key
    if body.key_type == "gemini":
        # Override hashing: use base64 encode so we can retrieve the key
        body = ApiKeyCreate(
            name=body.name,
            key_type=body.key_type,
            raw_key=body.raw_key,
        )
        # We'll intercept the hashing in the service for gemini keys
        # by pre-encoding the key before passing it
        import base64
        encoded_raw = encode_gemini_key(original_raw)
        # Patch: temporarily set raw_key to our encoded version
        # The service will call _hash_key(encoded_raw) which stores it as-is
        # This is handled by the encode_gemini_key prefix "b64$" detection in the service
        body = ApiKeyCreate(
            name=body.name,
            key_type=body.key_type,
            raw_key=encoded_raw,  # service stores this directly as hashed_key
        )
        # Override key_prefix to use real raw key prefix
        result = await _create_with_raw_prefix(db, body, original_raw)
    else:
        try:
            result = await create_api_key(db, body)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    logger.info("API key created via HTTP: id=%d type=%s prefix=%s", result.id, result.key_type, result.key_prefix)
    return result


async def _create_with_raw_prefix(
    db: AsyncSession,
    body: ApiKeyCreate,
    original_raw: str,
) -> ApiKeyCreatedOut:
    """Create a Gemini key, ensuring key_prefix uses the original raw key."""
    from app.models.entities import ApiKey, ApiKeyType
    from app.schemas.api_key import ApiKeyCreatedOut
    from app.services.api_key_service import _mask_key

    key_prefix = original_raw[:8]
    hashed = body.raw_key  # already encoded as "b64$..."

    key = ApiKey(
        name=body.name,
        key_type=ApiKeyType.gemini,
        key_prefix=key_prefix,
        hashed_key=hashed,
        is_active=True,
        created_by=None,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)

    return ApiKeyCreatedOut(
        id=key.id,
        name=key.name,
        key_type=key.key_type.value,
        key_prefix=key.key_prefix,
        is_active=key.is_active,
        created_by=key.created_by,
        last_used_at=key.last_used_at,
        created_at=key.created_at,
        masked_key=_mask_key(original_raw),
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_api_key(
    key_id: int,
    db: AsyncSession = Depends(get_db),
) -> None:
    """Soft-delete (deactivate) an API key. Returns 404 if not found."""
    deleted = await delete_api_key(db, key_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key {key_id} not found",
        )
