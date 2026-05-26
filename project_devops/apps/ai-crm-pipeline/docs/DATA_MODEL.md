# Data Model — CRM Pipeline

---

## 1. PostgreSQL

**Database:** `crm_db` (tách `platform_db` — init script Task 3.4)  
**User:** `crm_user` / password từ secret file

### Table: `leads`

| Column | Type | Note |
|--------|------|------|
| `id` | UUID PK | `gen_random_uuid()` |
| `message_id` | VARCHAR(128) UNIQUE | Idempotency |
| `channel` | VARCHAR(32) | facebook, tiktok, shopee, generic |
| `raw_text` | TEXT | Tin nhắn gốc |
| `customer_name` | VARCHAR(255) NULL | Từ LLM |
| `phone` | VARCHAR(64) NULL | |
| `product_interest` | VARCHAR(512) NULL | |
| `urgency` | VARCHAR(16) | low, medium, high, critical |
| `sentiment` | VARCHAR(16) | positive, neutral, negative |
| `intent` | VARCHAR(64) | purchase, inquiry, cancel_order, complaint, other |
| `language` | VARCHAR(16) NULL | ISO hint |
| `summary` | TEXT NULL | LLM tóm tắt |
| `alert_sent` | BOOLEAN DEFAULT false | |
| `alert_type` | VARCHAR(32) NULL | hot_lead, negative_sentiment, ... |
| `llm_model` | VARCHAR(64) | gemini-2.5-flash |
| `processed_at` | TIMESTAMPTZ | |
| `created_at` | TIMESTAMPTZ DEFAULT now() | |
| `auto_reply_sent` | BOOLEAN DEFAULT false | Phase 4 — Gemini CS reply |
| `auto_reply_content` | TEXT NULL | Reply body shown in demo UI |
| `auto_reply_at` | TIMESTAMPTZ NULL | When auto-reply was sent |
| `order_id` | VARCHAR(64) NULL | Shopee / marketplace order ref |
| `shop_id` | VARCHAR(128) NULL | Shop identifier from webhook |
| `locale` | VARCHAR(16) NULL | e.g. `tl-PH`, `id-ID`, `ms-MY` |

**Indexes:**
- `idx_leads_urgency` ON (`urgency`) WHERE urgency IN ('high','critical')
- `idx_leads_processed_at` ON (`processed_at` DESC)
- `idx_leads_channel_processed` ON (`channel`, `processed_at` DESC)

**Migration:** `project_devops/platform/config/postgres/init/05-crm-demo-migration.sh`

### Table: `processing_log`

| Column | Type | Note |
|--------|------|------|
| `id` | BIGSERIAL PK | |
| `message_id` | VARCHAR(128) | |
| `stage` | VARCHAR(32) | enqueue, llm, persist, alert |
| `status` | VARCHAR(16) | ok, error |
| `detail` | TEXT NULL | |
| `created_at` | TIMESTAMPTZ DEFAULT now() | |

---

## 2. Init script (Task 3.4)

**File:** `project_devops/platform/config/postgres/init/04-crm-init.sh`

```sql
-- Pseudocode — Cursor viết file shell heredoc
CREATE DATABASE crm_db;
CREATE USER crm_user WITH PASSWORD '...';
GRANT ALL ON DATABASE crm_db TO crm_user;
\c crm_db
-- CREATE TABLE leads ...
-- CREATE TABLE processing_log ...
```

Password: đọc từ `/run/secrets/crm_db_password` khi container init (pattern Odoo scripts).

---

## 3. Redis keys

| Key | Type | Purpose |
|-----|------|---------|
| `crm:queue:messages` | LIST | Job queue (LPUSH / BRPOP) |
| `crm:queue:dlq` | LIST | Failed jobs after retries |
| `crm:dedup:{message_id}` | STRING | "1", TTL 86400s |
| `crm:events:leads` | PUB/SUB | SSE fan-out — worker publishes after persist / auto-reply |

**Max queue length:** 10000 — khi đầy, ingestion trả `503` (backpressure).

---

## 4. LLM output JSON schema

Worker **bắt buộc** parse JSON khớp schema (Gemini `responseMimeType: application/json`).

```json
{
  "customer_name": "Maria",
  "phone": "+639171234567",
  "product_interest": "Vitamin C serum",
  "urgency": "high",
  "sentiment": "negative",
  "intent": "cancel_order",
  "language": "tl",
  "summary": "Customer angry about delayed order #8821, wants cancellation."
}
```

**Enum validation (worker):**

| Field | Allowed |
|-------|---------|
| urgency | low, medium, high, critical |
| sentiment | positive, neutral, negative |
| intent | purchase, inquiry, cancel_order, complaint, other |

Invalid enum → coerce `urgency=medium`, log warning, vẫn persist.

---

## 5. Gemini prompt template (Task 3.3)

```
You are a CRM data extraction engine for Southeast Asian e-commerce.
Input message may be Tagalog, Indonesian, English, or mixed slang.
Extract structured fields. Output ONLY valid JSON matching this schema:
{customer_name, phone, product_interest, urgency, sentiment, intent, language, summary}
Rules:
- urgency=critical if cancel/refund/chargeback anger or legal threat
- intent=cancel_order if user wants to cancel
- sentiment=negative if insults or strong dissatisfaction
Message: {{raw_text}}
Channel: {{channel}}
```

**Env:** đọc từ **repo root `.env`** (cùng `agentic-ai-api`): `LLM_PROVIDER`, `GEMINI_API_KEY`, `GEMINI_MODEL=gemini-2.5-flash`, `GEMINI_API_VERSION=v1beta`, …

**Client:** `crm-ai-worker/src/geminiProvider.py` + `providerFactory.py` — ports of `ai-agent/src/llm/geminiProvider.js` and `providerFactory.js`.

---

## 6. Worker DB flow

```
BRPOP queue → call Gemini → validate JSON → INSERT leads → INSERT processing_log
→ evaluate ALERT_RULES → UPDATE leads.alert_sent
```

Connection env (worker):
```
CRM_DATABASE_URL=postgresql://crm_user:***@platform-postgres:5432/crm_db
REDIS_URL=redis://platform-redis:6379/0
```

---

## 7. Sample queries (demo / Grafana)

```sql
SELECT message_id, channel, urgency, sentiment, intent, alert_sent,
       auto_reply_sent, auto_reply_content, processed_at
FROM leads ORDER BY processed_at DESC LIMIT 10;
```

```sql
SELECT message_id, channel, order_id, locale, auto_reply_sent, auto_reply_content
FROM leads WHERE channel = 'shopee' ORDER BY processed_at DESC LIMIT 5;
```

```sql
SELECT COUNT(*) FILTER (WHERE urgency IN ('high','critical')) AS hot_leads
FROM leads WHERE processed_at > now() - interval '1 hour';
```
