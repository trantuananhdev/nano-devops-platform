"""Read API + demo proxy + SSE for TNT Command Center."""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Any, Optional

import psycopg2
import psycopg2.extras
import redis.asyncio as redis
from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field
from sse_starlette.sse import EventSourceResponse

from config import CRM_DEMO_API_KEY, DATABASE_URL, EVENTS_CHANNEL, QUEUE_KEY, REDIS_URL
from demo_scenarios import list_scenarios_public, run_traffic_burst
from demo_templates import build_webhook_body, pick_template

router = APIRouter(prefix="/api/v1", tags=["read-api"])


def verify_demo_key(x_demo_key: Optional[str]) -> None:
    if not CRM_DEMO_API_KEY:
        return
    if x_demo_key != CRM_DEMO_API_KEY:
        raise HTTPException(status_code=401, detail={"status": "error", "code": "unauthorized"})


def db_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def row_to_lead(row: dict[str, Any]) -> dict[str, Any]:
    for key in ("processed_at", "created_at", "auto_reply_at"):
        val = row.get(key)
        if val and hasattr(val, "isoformat"):
            row[key] = val.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return dict(row)


@router.get("/leads")
def list_leads(
    limit: int = Query(50, ge=1, le=200),
    channel: Optional[str] = None,
    urgency: Optional[str] = None,
    since: Optional[str] = None,
) -> list[dict[str, Any]]:
    clauses = ["1=1"]
    params: list[Any] = []
    if channel:
        clauses.append("channel = %s")
        params.append(channel)
    if urgency:
        clauses.append("urgency = %s")
        params.append(urgency)
    if since:
        clauses.append("processed_at >= %s::timestamptz")
        params.append(since)
    params.append(limit)
    sql = f"""
        SELECT message_id, channel, raw_text, customer_name, phone, product_interest,
               urgency, sentiment, intent, language, summary, alert_sent, alert_type,
               auto_reply_sent, auto_reply_content, auto_reply_at,
               order_id, shop_id, locale, processed_at, created_at
        FROM leads
        WHERE {' AND '.join(clauses)}
        ORDER BY processed_at DESC
        LIMIT %s
    """
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            rows = cur.fetchall()
    return [row_to_lead(r) for r in rows]


@router.get("/leads/{message_id}")
def get_lead(message_id: str) -> dict[str, Any]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT message_id, channel, raw_text, customer_name, phone, product_interest,
                       urgency, sentiment, intent, language, summary, alert_sent, alert_type,
                       auto_reply_sent, auto_reply_content, auto_reply_at,
                       order_id, shop_id, locale, processed_at, created_at
                FROM leads WHERE message_id = %s
                """,
                (message_id,),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    return row_to_lead(row)


@router.get("/alerts")
def list_alerts(limit: int = Query(20, ge=1, le=100)) -> list[dict[str, Any]]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT message_id, channel, urgency, sentiment, intent, summary,
                       alert_type, processed_at
                FROM leads
                WHERE alert_sent = true
                  AND processed_at > now() - interval '24 hours'
                ORDER BY processed_at DESC
                LIMIT %s
                """,
                (limit,),
            )
            rows = cur.fetchall()
    return [row_to_lead(r) for r in rows]


@router.get("/queue/status")
async def queue_status() -> dict[str, Any]:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        depth = await r.llen(QUEUE_KEY)
        return {
            "depth": int(depth),
            "queue_key": QUEUE_KEY,
            "as_of": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    finally:
        await r.aclose()


@router.get("/metrics/summary")
def metrics_summary() -> dict[str, Any]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    COUNT(*) FILTER (WHERE processed_at > now() - interval '1 hour') AS processed_1h,
                    COUNT(*) FILTER (WHERE processed_at > now() - interval '24 hours') AS processed_24h,
                    COUNT(*) FILTER (WHERE alert_sent AND processed_at > now() - interval '24 hours') AS alerts_24h,
                    COUNT(*) FILTER (WHERE auto_reply_sent AND processed_at > now() - interval '24 hours') AS auto_replies_24h,
                    COUNT(*) FILTER (WHERE urgency IN ('high','critical') AND processed_at > now() - interval '1 hour') AS hot_1h
                FROM leads
                """
            )
            agg = cur.fetchone() or {}
            cur.execute(
                """
                SELECT channel, COUNT(*) AS cnt
                FROM leads
                WHERE processed_at > now() - interval '24 hours'
                GROUP BY channel
                ORDER BY cnt DESC
                """
            )
            by_channel = {r["channel"]: r["cnt"] for r in cur.fetchall()}
    return {
        "processed_1h": int(agg.get("processed_1h") or 0),
        "processed_24h": int(agg.get("processed_24h") or 0),
        "alerts_24h": int(agg.get("alerts_24h") or 0),
        "auto_replies_24h": int(agg.get("auto_replies_24h") or 0),
        "hot_leads_1h": int(agg.get("hot_1h") or 0),
        "by_channel_24h": by_channel,
        "as_of": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


class DemoSendBody(BaseModel):
    template_id: Optional[str] = None
    channel: str = Field(..., min_length=1)
    category: Optional[str] = None
    overrides: Optional[dict[str, Any]] = None


class TrafficBurstBody(BaseModel):
    scenario_id: str = Field(..., min_length=1)


@router.get("/demo/scenarios")
def demo_scenarios_list(
    x_demo_key: Optional[str] = Header(None, alias="X-Demo-Key"),
) -> list[dict[str, Any]]:
    verify_demo_key(x_demo_key)
    return list_scenarios_public()


@router.post("/demo/traffic-burst")
async def demo_traffic_burst(
    body: TrafficBurstBody,
    x_demo_key: Optional[str] = Header(None, alias="X-Demo-Key"),
) -> dict[str, Any]:
    verify_demo_key(x_demo_key)
    from main import handle_webhook

    try:
        return await run_traffic_burst(body.scenario_id, handle_webhook)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/demo/send")
async def demo_send(
    body: DemoSendBody,
    x_demo_key: Optional[str] = Header(None, alias="X-Demo-Key"),
) -> dict[str, Any]:
    verify_demo_key(x_demo_key)
    from main import handle_webhook, WebhookBody

    template = pick_template(body.channel, body.template_id, body.category)
    payload = build_webhook_body(template, body.channel, body.overrides)
    webhook_body = WebhookBody(**payload)
    return await handle_webhook(body.channel, webhook_body, x_webhook_secret=None)


async def _sse_generator(r: redis.Redis):
    pubsub = r.pubsub()
    await pubsub.subscribe(EVENTS_CHANNEL)
    try:
        while True:
            try:
                msg = await asyncio.wait_for(
                    pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0),
                    timeout=15.0,
                )
            except asyncio.TimeoutError:
                msg = None
            if msg and msg.get("type") == "message":
                data = msg.get("data")
                if isinstance(data, bytes):
                    data = data.decode()
                yield {"event": "lead", "data": data}
            else:
                yield {"comment": "ping"}
    finally:
        await pubsub.unsubscribe(EVENTS_CHANNEL)
        await pubsub.aclose()


@router.get("/events/stream")
async def events_stream() -> EventSourceResponse:
    r = redis.from_url(REDIS_URL, decode_responses=True)

    async def event_generator():
        try:
            async for item in _sse_generator(r):
                if "data" in item:
                    yield {"event": item.get("event", "lead"), "data": item["data"]}
                else:
                    yield {"comment": "ping"}
        finally:
            await r.aclose()

    return EventSourceResponse(event_generator(), ping=15)
