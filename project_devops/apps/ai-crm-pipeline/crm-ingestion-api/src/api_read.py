"""Read API + demo proxy + SSE — AI CRM Pipeline (BĐS Quản lý Lead)."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Optional, List

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
logger = logging.getLogger(__name__)

LEADS_SELECT = """
    message_id, channel, raw_text, customer_name, phone, email, product_interest,
    property_type, location, transaction_type, budget_range, bedroom_count,
    urgency, sentiment, intent, language, summary, alert_sent, alert_type,
    auto_reply_sent, auto_reply_content, auto_reply_at,
    order_id, shop_id, locale, processed_at, created_at, updated_at,
    kanban_stage, chat_history, ai_manager_note, tags, notes,
    assigned_to, source, company, website, address, city, country, description, last_contacted_at
"""


# --- Pydantic Models for new endpoints ---

class ActivityCreate(BaseModel):
    type: str = Field(..., min_length=1, max_length=32)
    title: str = Field(..., min_length=1, max_length=256)
    content: Optional[str] = None
    due_date: Optional[str] = None
    created_by: str = Field(..., min_length=1, max_length=128)

class ActivityUpdate(BaseModel):
    type: Optional[str] = None
    title: Optional[str] = None
    content: Optional[str] = None
    due_date: Optional[str] = None
    completed: Optional[bool] = None

class DealCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=256)
    amount: Optional[float] = None
    currency: str = Field(default="VND", min_length=1, max_length=16)
    probability: float = Field(default=50.0, ge=0.0, le=100.0)
    close_date: Optional[str] = None
    description: Optional[str] = None

class DealUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    probability: Optional[float] = None
    close_date: Optional[str] = None
    description: Optional[str] = None

class NoteCreate(BaseModel):
    content: str = Field(..., min_length=1)
    created_by: str = Field(..., min_length=1, max_length=128)

class TagsUpdate(BaseModel):
    tags: List[str] = Field(default_factory=list)


def verify_demo_key(x_demo_key: Optional[str]) -> None:
    if not CRM_DEMO_API_KEY:
        return
    if x_demo_key != CRM_DEMO_API_KEY:
        raise HTTPException(status_code=401, detail={"status": "error", "code": "unauthorized"})


def db_conn():
    return psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)


def row_to_lead(row: dict[str, Any]) -> dict[str, Any]:
    for key in ("processed_at", "created_at", "auto_reply_at", "last_contacted_at", "updated_at"):
        val = row.get(key)
        if val and hasattr(val, "isoformat"):
            row[key] = val.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    # Convert JSONB to dict/list if needed
    for json_key in ("chat_history", "tags", "notes", "activities", "deals"):
        json_val = row.get(json_key)
        if json_val and isinstance(json_val, str):
            try:
                row[json_key] = json.loads(json_val)
            except (json.JSONDecodeError, TypeError):
                pass
        # Ensure defaults
        if row.get(json_key) is None:
            row[json_key] = [] if json_key in ("tags", "notes", "activities", "deals") else None
    # Ensure BĐS fields are present with defaults
    for bds_field in ("transaction_type", "budget_range", "bedroom_count"):
        if bds_field not in row:
            row[bds_field] = None
    return dict(row)


@router.get("/leads")
def list_leads(
    limit: int = Query(50, ge=1, le=200),
    channel: Optional[str] = None,
    urgency: Optional[str] = None,
    since: Optional[str] = None,
    kanban_stage: Optional[str] = None,
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
    if kanban_stage:
        clauses.append("kanban_stage = %s")
        params.append(kanban_stage)
    params.append(limit)
    sql = f"""
        SELECT {LEADS_SELECT}
        FROM leads
        WHERE {' AND '.join(clauses)}
        ORDER BY processed_at DESC
        LIMIT %s
    """
    try:
        with db_conn() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params)
                rows = cur.fetchall()
        return [row_to_lead(r) for r in rows]
    except Exception as exc:
        logger.exception("list_leads failed: %s", exc)
        raise HTTPException(
            status_code=503,
            detail={"status": "error", "code": "db_unavailable", "message": str(exc)[:200]},
        ) from exc


@router.get("/leads/{message_id}")
def get_lead(message_id: str) -> dict[str, Any]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"SELECT {LEADS_SELECT} FROM leads WHERE message_id = %s",
                (message_id,),
            )
            row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    return row_to_lead(row)


# --- Activities Endpoints ---

@router.get("/leads/{message_id}/activities")
def list_activities(message_id: str) -> list[dict[str, Any]]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, lead_id, type, title, content, created_at, due_date, completed, created_by
                FROM lead_activities
                WHERE lead_id = %s
                ORDER BY created_at DESC
                """,
                (message_id,),
            )
            rows = cur.fetchall()
    # Convert datetime fields
    for row in rows:
        for key in ("created_at", "due_date"):
            val = row.get(key)
            if val and hasattr(val, "isoformat"):
                row[key] = val.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return list(rows) if rows else []


@router.post("/leads/{message_id}/activities")
def create_activity(message_id: str, body: ActivityCreate) -> dict[str, Any]:
    activity_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO lead_activities (id, lead_id, type, title, content, created_at, due_date, completed, created_by)
                VALUES (%s, %s, %s, %s, %s, %s, %s, false, %s)
                RETURNING *
                """,
                (activity_id, message_id, body.type, body.title, body.content, now, body.due_date, body.created_by),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create activity")
    # Convert datetime
    for key in ("created_at", "due_date"):
        val = row.get(key)
        if val and hasattr(val, "isoformat"):
            row[key] = val.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return dict(row)


@router.put("/leads/{message_id}/activities/{activity_id}")
def update_activity(message_id: str, activity_id: str, body: ActivityUpdate) -> dict[str, Any]:
    update_fields = []
    params = []
    for field in ["type", "title", "content", "due_date", "completed"]:
        val = getattr(body, field)
        if val is not None:
            update_fields.append(f"{field} = %s")
            params.append(val)
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    params.append(activity_id)
    params.append(message_id)
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE lead_activities
                SET {', '.join(update_fields)}
                WHERE id = %s AND lead_id = %s
                RETURNING *
                """,
                params,
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Activity not found")
    for key in ("created_at", "due_date"):
        val = row.get(key)
        if val and hasattr(val, "isoformat"):
            row[key] = val.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return dict(row)


@router.delete("/leads/{message_id}/activities/{activity_id}")
def delete_activity(message_id: str, activity_id: str):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM lead_activities WHERE id = %s AND lead_id = %s",
                (activity_id, message_id),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Activity not found")
        conn.commit()
    return {"status": "success", "id": activity_id}


# --- Deals Endpoints ---

@router.get("/leads/{message_id}/deals")
def list_deals(message_id: str) -> list[dict[str, Any]]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, lead_id, name, amount, currency, probability, close_date, description
                FROM deals
                WHERE lead_id = %s
                ORDER BY id DESC
                """,
                (message_id,),
            )
            rows = cur.fetchall()
    for row in rows:
        for key in ("close_date",):
            val = row.get(key)
            if val and hasattr(val, "isoformat"):
                row[key] = val.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return list(rows) if rows else []


@router.post("/leads/{message_id}/deals")
def create_deal(message_id: str, body: DealCreate) -> dict[str, Any]:
    deal_id = str(uuid.uuid4())
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO deals (id, lead_id, name, amount, currency, probability, close_date, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING *
                """,
                (deal_id, message_id, body.name, body.amount, body.currency, body.probability, body.close_date, body.description),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=500, detail="Failed to create deal")
    for key in ("close_date",):
        val = row.get(key)
        if val and hasattr(val, "isoformat"):
            row[key] = val.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return dict(row)


@router.put("/leads/{message_id}/deals/{deal_id}")
def update_deal(message_id: str, deal_id: str, body: DealUpdate) -> dict[str, Any]:
    update_fields = []
    params = []
    for field in ["name", "amount", "currency", "probability", "close_date", "description"]:
        val = getattr(body, field)
        if val is not None:
            update_fields.append(f"{field} = %s")
            params.append(val)
    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")
    params.append(deal_id)
    params.append(message_id)
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE deals
                SET {', '.join(update_fields)}
                WHERE id = %s AND lead_id = %s
                RETURNING *
                """,
                params,
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Deal not found")
    for key in ("close_date",):
        val = row.get(key)
        if val and hasattr(val, "isoformat"):
            row[key] = val.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return dict(row)


@router.delete("/leads/{message_id}/deals/{deal_id}")
def delete_deal(message_id: str, deal_id: str):
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM deals WHERE id = %s AND lead_id = %s",
                (deal_id, message_id),
            )
            if cur.rowcount == 0:
                raise HTTPException(status_code=404, detail="Deal not found")
        conn.commit()
    return {"status": "success", "id": deal_id}


# --- Notes Endpoints ---

@router.post("/leads/{message_id}/notes")
def add_note(message_id: str, body: NoteCreate) -> dict[str, Any]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads
                SET notes = COALESCE(notes, '[]'::jsonb) || jsonb_build_object('id', %s, 'content', %s, 'created_by', %s, 'created_at', %s)
                WHERE message_id = %s
                RETURNING message_id, notes
                """,
                (str(uuid.uuid4()), body.content, body.created_by, datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), message_id),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    return row_to_lead(row)


# --- Tags Endpoints ---

@router.put("/leads/{message_id}/tags")
def update_tags(message_id: str, body: TagsUpdate) -> dict[str, Any]:
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE leads
                SET tags = %s::jsonb, updated_at = %s
                WHERE message_id = %s
                RETURNING message_id, tags, updated_at
                """,
                (json.dumps(body.tags), datetime.now(timezone.utc), message_id),
            )
            row = cur.fetchone()
        conn.commit()
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    return row_to_lead(row)


# --- Lead Update Endpoint ---

class LeadUpdate(BaseModel):
    customer_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    product_interest: Optional[str] = None
    property_type: Optional[str] = None
    location: Optional[str] = None
    assigned_to: Optional[str] = None
    source: Optional[str] = None
    company: Optional[str] = None
    website: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None
    ai_manager_note: Optional[str] = None


@router.put("/leads/{message_id}")
def update_lead(message_id: str, body: LeadUpdate) -> dict[str, Any]:
    update_fields = ["updated_at = %s"]
    params = [datetime.now(timezone.utc)]
    for field in ["customer_name", "phone", "email", "product_interest", "property_type", "location", "assigned_to", "source", "company", "website", "address", "city", "country", "description", "ai_manager_note"]:
        val = getattr(body, field)
        if val is not None:
            update_fields.append(f"{field} = %s")
            params.append(val)
    params.append(message_id)
    with db_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                UPDATE leads
                SET {', '.join(update_fields)}
                WHERE message_id = %s
                RETURNING *
                """,
                params,
            )
            row = cur.fetchone()
        conn.commit()
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
        result = await run_traffic_burst(body.scenario_id, handle_webhook)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    from burst_summary import schedule_burst_summary

    asyncio.create_task(
        schedule_burst_summary(
            body.scenario_id,
            result.get("title_vi") or body.scenario_id,
            result.get("message_ids") or [],
        )
    )
    result["traffic_summary_pending"] = True
    return result


@router.get("/traffic/summary")
def traffic_summary(
    scenario_id: Optional[str] = Query(None),
    x_demo_key: Optional[str] = Header(None, alias="X-Demo-Key"),
) -> dict[str, Any]:
    verify_demo_key(x_demo_key)
    from burst_summary import get_latest_summary

    row = get_latest_summary(scenario_id)
    if not row:
        raise HTTPException(status_code=404, detail="No traffic summary yet")
    return row


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


class UpdateLeadStageBody(BaseModel):
    kanban_stage: str = Field(..., min_length=1, max_length=32)
    ai_manager_note: Optional[str] = None


@router.put("/leads/{message_id}/stage")
async def update_lead_stage(
    message_id: str,
    body: UpdateLeadStageBody,
    x_demo_key: Optional[str] = Header(None, alias="X-Demo-Key"),
) -> dict[str, Any]:
    verify_demo_key(x_demo_key)
    
    with db_conn() as conn:
        with conn.cursor() as cur:
            update_fields = ["kanban_stage = %s"]
            params = [body.kanban_stage]
            
            if body.ai_manager_note is not None:
                update_fields.append("ai_manager_note = %s")
                params.append(body.ai_manager_note)
            
            params.append(message_id)
            
            cur.execute(
                f"""
                UPDATE leads 
                SET {', '.join(update_fields)}
                WHERE message_id = %s
                RETURNING message_id, kanban_stage, ai_manager_note
                """,
                params,
            )
            row = cur.fetchone()
        conn.commit()
    
    if not row:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    return row_to_lead(row)


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
