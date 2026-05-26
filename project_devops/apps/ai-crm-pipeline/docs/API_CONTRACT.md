# API Contract — crm-ingestion-api

**Base URL (lab):** `https://crm-ingest.nano.platform`  
**Internal:** `http://platform-crm-ingestion:8080`

---

## 1. Principles

1. **Never block on LLM** — ingestion chỉ ghi queue.
2. **Always acknowledge** — HTTP `200` khi enqueue thành công (kể cả duplicate `message_id`).
3. **Minimal validation** — thiếu `raw_text` → `400`; lỗi hạ tầng → `503`.

---

## 2. Endpoints

### `GET /health`

**Response 200:**
```json
{
  "status": "healthy",
  "redis": "up",
  "version": "1.0.0"
}
```

**Response 503:** Redis unreachable.

---

### `GET /metrics`

Prometheus text format (port 8080). See ARCHITECTURE metrics table.

---

### `POST /webhook/facebook`

Mô phỏng Facebook Messenger payload (đơn giản hóa cho demo).

**Headers:**
| Header | Required | Note |
|--------|----------|------|
| `Content-Type` | Yes | `application/json` |
| `X-Webhook-Secret` | If `CRM_WEBHOOK_SECRET` set | Must match |

**Body:**
```json
{
  "message_id": "fb-123456789",
  "sender_id": "user_998877",
  "page_id": "page_tnt_ph",
  "timestamp": "2026-05-25T10:00:00Z",
  "raw_text": "Hi po gusto ko po i-cancel order #8821 ang tagal na walang update 😡",
  "channel": "facebook",
  "locale": "tl-PH"
}
```

**Response 200:**
```json
{
  "status": "accepted",
  "job_id": "fb-123456789",
  "queued_at": "2026-05-25T10:00:01.123Z"
}
```

---

### `POST /webhook/tiktok`

**Body:**
```json
{
  "message_id": "tt-554433221",
  "sender_id": "tiktok_user_abc",
  "shop_id": "tnt_id_shopee_mirror",
  "timestamp": "2026-05-25T11:30:00Z",
  "raw_text": "Ka mau tanya harga serum vitamin C untuk kulit berminyak",
  "channel": "tiktok",
  "locale": "id-ID"
}
```

**Response:** Same shape as Facebook.

---

### `POST /webhook/generic`

Fallback cho integration test / curl demo.

**Body:**
```json
{
  "message_id": "gen-001",
  "raw_text": "Call me 09123456789 I need 2 boxes sunscreen urgent",
  "channel": "generic",
  "metadata": {"campaign": "mega_sale_2026"}
}
```

---

## 3. Queue job schema (Redis value)

Mỗi `LPUSH` vào `crm:queue:messages` là JSON string:

```json
{
  "job_id": "fb-123456789",
  "message_id": "fb-123456789",
  "channel": "facebook",
  "received_at": "2026-05-25T10:00:01.123Z",
  "payload": { }
}
```

`payload` = nguyên body webhook.

---

## 4. Error codes

| HTTP | Code | Khi nào |
|------|------|---------|
| 400 | `invalid_payload` | Thiếu `message_id` hoặc `raw_text` |
| 401 | `unauthorized` | Sai `X-Webhook-Secret` |
| 503 | `queue_unavailable` | Redis lỗi |
| 500 | `internal_error` | Unhandled (hiếm) |

**Error body:**
```json
{
  "status": "error",
  "code": "invalid_payload",
  "detail": "raw_text is required"
}
```

---

## 5. Idempotency

- Key: `message_id`
- Redis SET `crm:dedup:{message_id}` TTL 24h — nếu exists → `200 accepted` không push queue lần 2.
- Worker vẫn có unique constraint Postgres phòng trường hợp race.

---

## 6. Implementation notes (Cursor Task 3.2)

```python
# Pseudocode — NOT optional pattern
@app.post("/webhook/{channel}")
async def webhook(channel: str, body: WebhookBody, ...):
    await validate_secret(...)
    if await dedup_exists(body.message_id):
        return {"status": "accepted", "job_id": body.message_id, "duplicate": True}
    job = build_job(body, channel)
    await redis.lpush(QUEUE_KEY, job.json())
    await dedup_set(body.message_id)
    CRM_INGEST_REQUESTS.labels(channel=channel).inc()
    return {"status": "accepted", "job_id": body.message_id, ...}
```

Libraries: `fastapi`, `redis.asyncio`, `pydantic`, `prometheus_client`.

---

## 7. curl examples (for DEMO_RUNBOOK)

```bash
curl -sk -X POST https://crm-ingest.nano.platform/webhook/generic \
  -H "Content-Type: application/json" \
  -d '{"message_id":"demo-hot-1","raw_text":"Cancel order NOW very angry!!!","channel":"generic"}'
```

```bash
curl -sk https://crm-ingest.nano.platform/health
```

---

## 8. Read API (Phase 4 — Dashboard)

**Prefix:** `/api/v1`  
**CORS:** `https://crm-demo.nano.platform`, `http://localhost:5173`  
**Auth (optional lab):** header `X-Demo-Key` = `CRM_DEMO_API_KEY`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/leads` | `?limit=50&channel=&urgency=&since=` |
| GET | `/api/v1/leads/{message_id}` | Full lead + auto-reply |
| GET | `/api/v1/alerts` | `alert_sent=true` last 24h |
| GET | `/api/v1/metrics/summary` | Aggregates for metric cards |
| POST | `/api/v1/demo/send` | Proxy ingest from UI templates (1 tin) |
| GET | `/api/v1/demo/scenarios` | Danh sách kịch bản đổ traffic (tiếng Việt) |
| POST | `/api/v1/demo/traffic-burst` | Đổ lô tin theo `scenario_id` (mô phỏng traffic ập vào) |
| GET | `/api/v1/queue/status` | Độ sâu hàng đợi Redis |
| GET | `/api/v1/events/stream` | SSE — Redis channel `crm:events:leads` |

**`GET /api/v1/demo/scenarios`:** trả metadata `title_vi`, `description_vi`, `crm_stage_vi`, `ai_focus_vi`, `message_count`.

**`POST /api/v1/demo/traffic-burst`:**
```json
{ "scenario_id": "live_tiktok_surge" }
```
Response: `{ "status": "burst_started", "accepted_count", "message_ids", "total_planned" }`.

**`POST /api/v1/demo/send`:**
```json
{
  "template_id": "cancel_angry_tl",
  "channel": "facebook",
  "category": "cancel_order",
  "overrides": { "message_id": "optional-id" }
}
```

---

## 9. Shopee webhook (Phase 4)

### `POST /webhook/shopee`

**Body:**
```json
{
  "message_id": "sp-20260525-001",
  "sender_id": "buyer_my_7721",
  "order_id": "2405123456789",
  "shop_id": "tnt_my_official",
  "timestamp": "2026-05-25T14:00:00Z",
  "raw_text": "Boleh saya tahu bila barang sampai? Order ni dah 5 hari.",
  "channel": "shopee",
  "locale": "ms-MY"
}
```

**Response:** Same as Facebook (`200 accepted`).  
**Metric:** `crm_ingest_requests_total{channel="shopee"}`.
