"""T-16: preference_service — get/set per-user preferences in PostgreSQL.

Preferences are stored as (user_id, key) → value (JSONB).
Upsert uses INSERT ... ON CONFLICT DO UPDATE (PG dialect).
"""
import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import UserPreference

logger = logging.getLogger(__name__)


async def get_preferences(session: AsyncSession, user_id: int) -> dict[str, Any]:
    """Return all preferences for a user as {key: value} dict."""
    result = await session.execute(
        select(UserPreference).where(UserPreference.user_id == user_id)
    )
    rows = result.scalars().all()
    return {row.key: row.value for row in rows}


async def get_preference(
    session: AsyncSession, user_id: int, key: str
) -> Any | None:
    """Return one preference value or None."""
    result = await session.execute(
        select(UserPreference).where(
            UserPreference.user_id == user_id, UserPreference.key == key
        )
    )
    row = result.scalar_one_or_none()
    return row.value if row else None


async def set_preference(
    session: AsyncSession, user_id: int, key: str, value: Any
) -> UserPreference:
    """Upsert a preference. Returns the saved row."""
    # PostgreSQL UPSERT — idempotent on (user_id, key)
    stmt = (
        pg_insert(UserPreference)
        .values(user_id=user_id, key=key, value=value)
        .on_conflict_do_update(
            index_elements=["user_id", "key"],
            set_={"value": value},
        )
        .returning(UserPreference.id, UserPreference.user_id, UserPreference.key, UserPreference.value)
    )
    result = await session.execute(stmt)
    await session.commit()
    # RETURNING gives us a Row, not a mapped ORM object — re-fetch for clean return
    row_data = result.fetchone()
    logger.debug("Preference set: user=%d key=%s value=%s", user_id, key, value)
    # Return a lightweight detached row — callers only need key/value
    pref = UserPreference(
        id=row_data[0], user_id=row_data[1], key=row_data[2], value=row_data[3]
    )
    return pref


async def set_preferences_bulk(
    session: AsyncSession, user_id: int, prefs: dict[str, Any]
) -> list[UserPreference]:
    """Upsert multiple preferences at once. Returns saved rows."""
    rows = []
    for key, value in prefs.items():
        rows.append(await set_preference(session, user_id, key, value))
    return rows
