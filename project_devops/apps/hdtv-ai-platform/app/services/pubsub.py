import json
from typing import Any

import redis.asyncio as aioredis

from app.core.config import get_settings

CHANNEL_PREFIX = "appraisal:"


def channel_name(dossier_id: int) -> str:
    return f"{CHANNEL_PREFIX}{dossier_id}"


async def publish_event(dossier_id: int, event: dict[str, Any]) -> None:
    settings = get_settings()
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.publish(channel_name(dossier_id), json.dumps(event, default=str))
    finally:
        await client.aclose()


async def subscribe_events(dossier_id: int):
    settings = get_settings()
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    pubsub = client.pubsub()
    await pubsub.subscribe(channel_name(dossier_id))
    return client, pubsub
