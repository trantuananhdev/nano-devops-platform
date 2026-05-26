"""
crm-ai-worker — Redis consumer, Gemini extraction, Postgres CRM, alerts.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any

import psycopg2
import redis.asyncio as redis

from alerts import maybe_send_alert
from auto_reply import (
    generate_reply,
    persist_auto_reply,
    should_auto_reply,
)
from config import (
    AUTO_REPLY_ENABLED,
    CRM_WORKER_JOB_DELAY_MS,
    DATABASE_URL,
    DLQ_KEY,
    GEMINI_MODEL,
    MAX_RETRIES,
    METRICS_PORT,
    QUEUE_KEY,
    REDIS_URL,
)
from events import publish_lead_event
from llm_gemini import extract_fields
from metrics import AUTO_REPLY_TOTAL, JOBS_PROCESSED, QUEUE_DEPTH, start_metrics_server

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def log_stage(conn, message_id: str, stage: str, status: str, detail: str = "") -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO processing_log (message_id, stage, status, detail)
            VALUES (%s, %s, %s, %s)
            """,
            (message_id, stage, status, detail[:2000]),
        )
    conn.commit()


def persist_lead(conn, job: dict[str, Any], extracted: dict[str, Any]) -> dict[str, Any]:
    payload = job.get("payload") or {}
    raw_text = payload.get("raw_text", "")
    channel = job.get("channel", "generic")
    message_id = job["message_id"]
    processed_at = utc_now_iso()
    order_id = payload.get("order_id")
    shop_id = payload.get("shop_id")
    locale = payload.get("locale")

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO leads (
                message_id, channel, raw_text, customer_name, phone,
                product_interest, urgency, sentiment, intent, language, summary,
                order_id, shop_id, locale, llm_model, processed_at
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (message_id) DO UPDATE SET
                urgency = EXCLUDED.urgency,
                sentiment = EXCLUDED.sentiment,
                intent = EXCLUDED.intent,
                summary = EXCLUDED.summary,
                order_id = EXCLUDED.order_id,
                shop_id = EXCLUDED.shop_id,
                locale = EXCLUDED.locale,
                processed_at = EXCLUDED.processed_at
            RETURNING id::text
            """,
            (
                message_id,
                channel,
                raw_text,
                extracted.get("customer_name"),
                extracted.get("phone"),
                extracted.get("product_interest"),
                extracted["urgency"],
                extracted["sentiment"],
                extracted["intent"],
                extracted.get("language"),
                extracted.get("summary"),
                order_id,
                shop_id,
                locale,
                GEMINI_MODEL,
                processed_at,
            ),
        )
    conn.commit()

    return {
        "message_id": message_id,
        "channel": channel,
        "raw_text": raw_text,
        **extracted,
        "processed_at": processed_at,
        "alert_sent": False,
        "alert_type": None,
        "auto_reply_sent": False,
        "auto_reply_content": None,
    }


def update_alert_flags(conn, message_id: str, alert_type: str | None) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE leads SET alert_sent = %s, alert_type = %s WHERE message_id = %s
            """,
            (bool(alert_type), alert_type, message_id),
        )
    conn.commit()


def _processing_event(job: dict[str, Any], channel: str, raw_text: str) -> dict[str, Any]:
    return {
        "message_id": job.get("message_id", "unknown"),
        "channel": channel,
        "raw_text": raw_text,
        "urgency": "pending",
        "sentiment": "pending",
        "intent": "processing",
        "summary": "Gemini đang phân tích tin nhắn…",
        "alert_sent": False,
        "auto_reply_sent": False,
    }


async def process_job(r: redis.Redis, job_raw: str) -> None:
    job = json.loads(job_raw)
    message_id = job.get("message_id", "unknown")
    # Retry count is embedded in job payload so it persists across re-queues
    retry_count = int(job.get("_retry_count", 0))
    payload = job.get("payload") or {}
    raw_text = payload.get("raw_text", "")
    channel = job.get("channel", "generic")

    publish_lead_event(_processing_event(job, channel, raw_text), "lead_processing")

    conn = psycopg2.connect(DATABASE_URL)
    try:
        log_stage(conn, message_id, "llm", "ok", "start")
        extracted = await asyncio.to_thread(extract_fields, raw_text, channel, payload)
        if payload.get("customer_name"):
            extracted["customer_name"] = payload["customer_name"]
        if payload.get("phone"):
            extracted["phone"] = payload["phone"]
        lead = persist_lead(conn, job, extracted)
        log_stage(conn, message_id, "persist", "ok", "")

        alert_type = await maybe_send_alert(r, lead)
        if alert_type:
            lead["alert_type"] = alert_type
            lead["alert_sent"] = True
            update_alert_flags(conn, message_id, alert_type)
            log_stage(conn, message_id, "alert", "ok", alert_type)
        else:
            log_stage(conn, message_id, "alert", "ok", "skipped")

        if AUTO_REPLY_ENABLED and should_auto_reply(extracted):
            try:
                reply = await asyncio.to_thread(
                    generate_reply, raw_text, extracted, channel
                )
                persist_auto_reply(conn, message_id, reply)
                lead["auto_reply_sent"] = True
                lead["auto_reply_content"] = reply
                log_stage(conn, message_id, "auto_reply", "ok", "")
                AUTO_REPLY_TOTAL.labels(status="sent").inc()
                publish_lead_event(lead, "auto_reply_sent")
            except Exception as ar_exc:
                logger.warning("Auto-reply failed %s: %s", message_id, ar_exc)
                AUTO_REPLY_TOTAL.labels(status="error").inc()
        else:
            AUTO_REPLY_TOTAL.labels(status="skipped").inc()

        publish_lead_event(lead, "lead_processed")
        JOBS_PROCESSED.labels(status="success").inc()
        logger.info("Processed message_id=%s urgency=%s", message_id, extracted.get("urgency"))
    except Exception as exc:
        logger.exception("Job failed message_id=%s: %s", message_id, exc)
        try:
            log_stage(conn, message_id, "error", "error", str(exc))
        except Exception:
            pass
        JOBS_PROCESSED.labels(status="fail").inc()

        if retry_count + 1 >= MAX_RETRIES:
            await r.lpush(DLQ_KEY, job_raw)
            logger.error("Moved to DLQ after %d retries: %s", retry_count + 1, message_id)
        else:
            # Embed incremented retry count back into the job for next attempt
            job["_retry_count"] = retry_count + 1
            updated_job_raw = json.dumps(job)
            # 429 rate-limit: back off 60s; other errors: exponential (2^n seconds)
            is_rate_limit = "429" in str(exc)
            backoff = 15 if is_rate_limit else (2 ** retry_count)
            logger.warning(
                "Requeue message_id=%s in %ds (attempt %d/%d, rate_limit=%s)",
                message_id, backoff, retry_count + 1, MAX_RETRIES, is_rate_limit,
            )
            asyncio.create_task(_delayed_requeue(r, updated_job_raw, backoff))
    finally:
        conn.close()


async def _delayed_requeue(r: redis.Redis, job_raw: str, delay_s: int) -> None:
    await asyncio.sleep(max(1, delay_s))
    await r.lpush(QUEUE_KEY, job_raw)


async def update_queue_depth(r: redis.Redis) -> None:
    depth = await r.llen(QUEUE_KEY)
    QUEUE_DEPTH.set(depth)


async def run_worker() -> None:
    start_metrics_server(METRICS_PORT)
    r = redis.from_url(REDIS_URL, decode_responses=True)
    from providerFactory import create_llm_provider

    llm = create_llm_provider()
    logger.info(
        "Worker started. Queue=%s model=%s (geminiProvider)",
        QUEUE_KEY,
        llm.model,
    )

    while True:
        await update_queue_depth(r)
        item = await r.brpop(QUEUE_KEY, timeout=5)
        if not item:
            continue
        _, job_raw = item
        await process_job(r, job_raw)
        if CRM_WORKER_JOB_DELAY_MS > 0:
            await asyncio.sleep(CRM_WORKER_JOB_DELAY_MS / 1000.0)


def main() -> None:
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker stopped")


if __name__ == "__main__":
    main()
