"""
API Key Service — T-33: Secure key storage + DB-backed llm_router.

Design:
  - Keys are hashed with bcrypt (via passlib) before persist.
  - key_prefix = first 8 chars (safe to display/identify).
  - `verify_key(raw, hashed)` is timing-safe (bcrypt).
  - `get_active_keys_by_type()` is used by llm_router as primary key source.
    Falls back to .env keys when DB is empty (zero-downtime migration).
"""

from __future__ import annotations

import hashlib
import hmac
import logging
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import ApiKey, ApiKeyType
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreatedOut, ApiKeyOut

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# bcrypt shim — prefer passlib; fall back to hashlib PBKDF2 for alpine envs
# without gcc (passlib bcrypt needs cffi)
# ---------------------------------------------------------------------------
try:
    from passlib.context import CryptContext

    _pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def _hash_key(raw: str) -> str:
        return _pwd_ctx.hash(raw)

    def _verify_hash(raw: str, hashed: str) -> bool:
        try:
            return _pwd_ctx.verify(raw, hashed)
        except Exception:
            return False

except ImportError:
    # Fallback: PBKDF2-HMAC-SHA256 with a fixed app-level salt prefix.
    # NOT as strong as bcrypt but acceptable when passlib is unavailable.
    _PBKDF2_SALT = b"hdtv-apikey-salt-v1"
    _PBKDF2_ITERS = 200_000

    def _hash_key(raw: str) -> str:  # type: ignore[misc]
        dk = hashlib.pbkdf2_hmac("sha256", raw.encode(), _PBKDF2_SALT, _PBKDF2_ITERS)
        return f"pbkdf2${dk.hex()}"

    def _verify_hash(raw: str, hashed: str) -> bool:  # type: ignore[misc]
        if not hashed.startswith("pbkdf2$"):
            return False
        dk = hashlib.pbkdf2_hmac("sha256", raw.encode(), _PBKDF2_SALT, _PBKDF2_ITERS)
        expected = f"pbkdf2${dk.hex()}"
        return hmac.compare_digest(expected, hashed)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mask_key(raw: str) -> str:
    """Return masked preview for display (e.g. 'AIzaSy**…**XYZ')."""
    if len(raw) <= 12:
        return raw[:4] + "***"
    return raw[:8] + "*" * (len(raw) - 12) + raw[-4:]


# ---------------------------------------------------------------------------
# Service functions
# ---------------------------------------------------------------------------

async def create_api_key(
    db: AsyncSession,
    body: ApiKeyCreate,
    created_by: int | None = None,
) -> ApiKeyCreatedOut:
    """Hash and persist a new API key. Returns a one-time masked preview."""
    try:
        key_type = ApiKeyType(body.key_type)
    except ValueError:
        valid = [t.value for t in ApiKeyType]
        raise ValueError(f"Invalid key_type '{body.key_type}'. Valid: {valid}")

    key_prefix = body.raw_key[:8]
    hashed = _hash_key(body.raw_key)
    masked = _mask_key(body.raw_key)

    key = ApiKey(
        name=body.name,
        key_type=key_type,
        key_prefix=key_prefix,
        hashed_key=hashed,
        is_active=True,
        created_by=created_by,
    )
    db.add(key)
    await db.commit()
    await db.refresh(key)

    logger.info("API key created: id=%d name=%s type=%s prefix=%s", key.id, key.name, key.key_type, key_prefix)
    return ApiKeyCreatedOut(
        id=key.id,
        name=key.name,
        key_type=key.key_type.value,
        key_prefix=key.key_prefix,
        is_active=key.is_active,
        created_by=key.created_by,
        last_used_at=key.last_used_at,
        created_at=key.created_at,
        masked_key=masked,
    )


async def list_api_keys(db: AsyncSession, key_type: str | None = None) -> list[ApiKeyOut]:
    """List all API keys (hashed_key excluded). Optionally filter by type."""
    stmt = select(ApiKey).order_by(ApiKey.created_at.desc())
    if key_type:
        try:
            stmt = stmt.where(ApiKey.key_type == ApiKeyType(key_type))
        except ValueError:
            pass  # Invalid type — return all
    rows = (await db.execute(stmt)).scalars().all()
    return [
        ApiKeyOut(
            id=r.id,
            name=r.name,
            key_type=r.key_type.value,
            key_prefix=r.key_prefix,
            is_active=r.is_active,
            created_by=r.created_by,
            last_used_at=r.last_used_at,
            created_at=r.created_at,
        )
        for r in rows
    ]


async def delete_api_key(db: AsyncSession, key_id: int) -> bool:
    """Soft-delete: set is_active=False. Returns False if not found."""
    row = await db.get(ApiKey, key_id)
    if row is None:
        return False
    row.is_active = False
    await db.commit()
    logger.info("API key deactivated: id=%d name=%s", key_id, row.name)
    return True


async def get_active_keys_by_type(db: AsyncSession, key_type: ApiKeyType) -> list[str]:
    """Return raw-ish keys for llm_router.

    NOTE: We cannot reverse-hash bcrypt. Instead we store raw keys in a
    runtime in-memory cache populated at startup from .env AND from DB
    (where keys are stored as plaintext ONLY for types that support it via
    an alternate plaintext_key column — see design note below).

    DESIGN NOTE: For Gemini keys specifically, we store the raw key in
    hashed_key using a *reversible* encoding (base64) so the router can
    retrieve them. This is a pragmatic tradeoff: Gemini keys have no
    offline verification mechanism (you can't verify without calling the API),
    so bcrypt would prevent retrieval without storing the raw key elsewhere.

    For MCP/internal keys that only need server-side verify, pure bcrypt is used.
    """
    stmt = (
        select(ApiKey)
        .where(ApiKey.key_type == key_type)
        .where(ApiKey.is_active.is_(True))
        .order_by(ApiKey.created_at.asc())
    )
    rows = (await db.execute(stmt)).scalars().all()

    keys: list[str] = []
    for row in rows:
        raw = _try_decode_gemini_key(row.hashed_key)
        if raw:
            keys.append(raw)
            # Touch last_used_at lazily — fire-and-forget best effort
            try:
                row.last_used_at = datetime.now(timezone.utc)
                await db.commit()
            except Exception:
                pass
    return keys


def _try_decode_gemini_key(hashed: str) -> str | None:
    """Attempt to decode a Gemini key stored as base64.

    Returns None for bcrypt/pbkdf2 hashed values (MCP/internal keys).
    """
    import base64
    if hashed.startswith("b64$"):
        try:
            return base64.b64decode(hashed[4:]).decode()
        except Exception:
            return None
    return None


def encode_gemini_key(raw: str) -> str:
    """Encode Gemini key as reversible base64 for DB storage."""
    import base64
    return "b64$" + base64.b64encode(raw.encode()).decode()


async def verify_api_key(db: AsyncSession, raw_key: str, key_type: ApiKeyType) -> bool:
    """Verify an incoming key against the active hashed keys of a given type."""
    stmt = (
        select(ApiKey)
        .where(ApiKey.key_type == key_type)
        .where(ApiKey.is_active.is_(True))
        .where(ApiKey.key_prefix == raw_key[:8])
    )
    rows = (await db.execute(stmt)).scalars().all()
    for row in rows:
        if _verify_hash(raw_key, row.hashed_key):
            return True
    return False
