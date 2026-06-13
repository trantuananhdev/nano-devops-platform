import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings

CHANNEL_PREFIX = "appraisal:"
NOTIF_PREFIX = "notifications:"


async def _make_client() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(settings.redis_url, decode_responses=True)


async def subscribe_user_notifications(user_id: int):
    """Subscribe to per-user notification channel.  Returns (client, pubsub)."""
    client = await _make_client()
    pubsub = client.pubsub()
    await pubsub.subscribe(f"{NOTIF_PREFIX}{user_id}")
    return client, pubsub


async def publish_user_notification(user_id: int, event: dict[str, Any]) -> None:
    """Publish a notification event to a specific user's channel."""
    client = await _make_client()
    try:
        await client.publish(f"{NOTIF_PREFIX}{user_id}", json.dumps(event, default=str))
    finally:
        await client.aclose()


def channel_name(dossier_id: int) -> str:
    return f"{CHANNEL_PREFIX}{dossier_id}"


async def publish_event(dossier_id: int, event: dict[str, Any]) -> None:
    client = await _make_client()
    try:
        await client.publish(channel_name(dossier_id), json.dumps(event, default=str))
    finally:
        await client.aclose()


async def subscribe_events(dossier_id: int):
    client = await _make_client()
    pubsub = client.pubsub()
    await pubsub.subscribe(channel_name(dossier_id))
    return client, pubsub
