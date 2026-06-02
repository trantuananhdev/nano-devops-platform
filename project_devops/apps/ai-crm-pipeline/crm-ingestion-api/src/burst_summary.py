"""Post–traffic-burst AI summary (Agent 1 — GEMINI_API_KEY_1)."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Optional

import httpx
import psycopg2
import psycopg2.extras
import redis.asyncio as redis

from config import CRM_SKIP_GEMINI, DATABASE_URL, EVENTS_CHANNEL, QUEUE_KEY, REDIS_URL

logger = logging.getLogger(__name__)

TRAFFIC_SYSTEM = """You are a CRM traffic analyst for Vietnamese real estate demo.
Given processed leads from a traffic burst, write an executive summary in Vietnamese.
Output JSON only:
{"title_vi": string, "summary_vi": string, "hot_leads": number, "channels": object, "recommendations": [string]}"""


def _agent1_key() -> str:
    key = os.getenv("GEMINI_API_KEY_1", "").strip().strip('"').strip("'")
    if not key:
        key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY_1 not set")
    return key


def _gemini_json(prompt: str) -> dict[str, Any]:
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    version = os.getenv("GEMINI_API_VERSION", "v1beta")
    url = (
        f"https://generativelanguage.googleapis.com/{version}/models/{model}:generateContent"
        f"?key={_agent1_key()}"
    )
    body = {
        "contents": [{"parts": [{"text": f"{TRAFFIC_SYSTEM}\n\n{prompt}"}]}],
        "generationConfig": {
            "temperature": 0.2,
            "maxOutputTokens": 2048,
            "responseMimeType": "application/json",
        },
    }
    with httpx.Client(timeout=60.0) as client:
        resp = client.post(url, json=body)
        resp.raise_for_status()
        text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        return json.loads(match.group()) if match else {}


def analyze_traffic_batch(scenario_title: str, leads: list[dict[str, Any]]) -> dict[str, Any]:
    if not leads:
        return {
            "title_vi": scenario_title,
            "summary_vi": "Chưa có lead nào được xử lý xong.",
            "hot_leads": 0,
            "channels": {},
            "recommendations": ["Chờ worker xử lý queue."],
            "lead_count": 0,
        }
    compact = [
        {
            "channel": L.get("channel"),
            "urgency": L.get("urgency"),
            "intent": L.get("intent"),
            "summary": (L.get("summary") or "")[:120],
        }
        for L in leads[:50]
    ]
    if not CRM_SKIP_GEMINI:
        try:
            parsed = _gemini_json(
                f"Scenario: {scenario_title}\nLeads ({len(leads)}):\n"
                f"{json.dumps(compact, ensure_ascii=False)}"
            )
            if parsed.get("summary_vi"):
                parsed["lead_count"] = len(leads)
                return parsed
        except Exception as exc:
            logger.warning("Agent 1 traffic summary failed: %s", exc)

    hot = sum(1 for L in leads if L.get("urgency") in ("high", "critical"))
    by_ch: dict[str, int] = {}
    for L in leads:
        ch = L.get("channel") or "unknown"
        by_ch[ch] = by_ch.get(ch, 0) + 1
    return {
        "title_vi": scenario_title,
        "summary_vi": f"Đã xử lý {len(leads)} lead, {hot} lead nóng (high/critical).",
        "hot_leads": hot,
        "channels": by_ch,
        "lead_count": len(leads),
        "recommendations": [
            "Ưu tiên gọi lead critical/high",
            "Theo dõi kênh có volume cao nhất",
        ],
    }


def _fetch_leads_by_ids(message_ids: list[str]) -> list[dict[str, Any]]:
    if not message_ids:
        return []
    with psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT message_id, channel, urgency, sentiment, intent, summary,
                       customer_name, property_type, location, processed_at
                FROM leads WHERE message_id = ANY(%s)
                ORDER BY processed_at DESC
                """,
                (message_ids,),
            )
            return [dict(r) for r in cur.fetchall()]


def _persist_summary(scenario_id: str, title: str, analysis: dict[str, Any]) -> None:
    with psycopg2.connect(DATABASE_URL) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO traffic_summaries (
                    scenario_id, title_vi, summary_vi, hot_leads, channels_json,
                    recommendations_json, lead_count, raw_json, created_at
                ) VALUES (%s, %s, %s, %s, %s::jsonb, %s::jsonb, %s, %s::jsonb, %s)
                ON CONFLICT (scenario_id) DO UPDATE SET
                    title_vi = EXCLUDED.title_vi,
                    summary_vi = EXCLUDED.summary_vi,
                    hot_leads = EXCLUDED.hot_leads,
                    channels_json = EXCLUDED.channels_json,
                    recommendations_json = EXCLUDED.recommendations_json,
                    lead_count = EXCLUDED.lead_count,
                    raw_json = EXCLUDED.raw_json,
                    created_at = EXCLUDED.created_at
                """,
                (
                    scenario_id,
                    analysis.get("title_vi") or title,
                    analysis.get("summary_vi", ""),
                    int(analysis.get("hot_leads") or 0),
                    json.dumps(analysis.get("channels") or {}),
                    json.dumps(analysis.get("recommendations") or []),
                    int(analysis.get("lead_count") or 0),
                    json.dumps(analysis),
                    datetime.now(timezone.utc),
                ),
            )
        conn.commit()


async def _wait_for_queue_drain(max_wait_s: int = 90) -> None:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        for _ in range(max_wait_s):
            if await r.llen(QUEUE_KEY) == 0:
                await asyncio.sleep(2)
                if await r.llen(QUEUE_KEY) == 0:
                    return
            await asyncio.sleep(1)
    finally:
        await r.aclose()


async def _publish_summary_event(scenario_id: str, analysis: dict[str, Any]) -> None:
    r = redis.from_url(REDIS_URL, decode_responses=True)
    try:
        payload = json.dumps(
            {"type": "traffic_summary", "scenario_id": scenario_id, **analysis},
            ensure_ascii=False,
        )
        await r.publish(EVENTS_CHANNEL, payload)
    finally:
        await r.aclose()


async def schedule_burst_summary(
    scenario_id: str,
    scenario_title: str,
    message_ids: list[str],
) -> None:
    try:
        await _wait_for_queue_drain()
        await asyncio.sleep(3)
        leads = _fetch_leads_by_ids(message_ids)
        analysis = analyze_traffic_batch(scenario_title, leads)
        _persist_summary(scenario_id, scenario_title, analysis)
        await _publish_summary_event(scenario_id, analysis)
        logger.info("Traffic summary ready for %s (%d leads)", scenario_id, len(leads))
    except Exception as exc:
        logger.exception("Burst summary failed %s: %s", scenario_id, exc)


def get_latest_summary(scenario_id: Optional[str] = None) -> Optional[dict[str, Any]]:
    with psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor) as conn:
        with conn.cursor() as cur:
            if scenario_id:
                cur.execute(
                    """
                    SELECT scenario_id, title_vi, summary_vi, hot_leads, channels_json,
                           recommendations_json, lead_count, created_at
                    FROM traffic_summaries WHERE scenario_id = %s
                    """,
                    (scenario_id,),
                )
            else:
                cur.execute(
                    """
                    SELECT scenario_id, title_vi, summary_vi, hot_leads, channels_json,
                           recommendations_json, lead_count, created_at
                    FROM traffic_summaries ORDER BY created_at DESC LIMIT 1
                    """
                )
            row = cur.fetchone()
    if not row:
        return None
    out = dict(row)
    channels = out.pop("channels_json", None) or {}
    recommendations = out.pop("recommendations_json", None) or []
    if isinstance(channels, str):
        try:
            channels = json.loads(channels)
        except json.JSONDecodeError:
            channels = {}
    if isinstance(recommendations, str):
        try:
            recommendations = json.loads(recommendations)
        except json.JSONDecodeError:
            recommendations = []
    out["channels"] = channels if isinstance(channels, dict) else {}
    out["recommendations"] = recommendations if isinstance(recommendations, list) else []
    if out.get("created_at"):
        out["created_at"] = out["created_at"].astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    return out
