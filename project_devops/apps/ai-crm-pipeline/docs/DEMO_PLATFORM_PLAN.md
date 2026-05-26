# DEMO PLATFORM PLAN — TNT Group Executive Demo

**Mục tiêu:** Một bản demo **hoành tráng**, không cần CLI, thuyết phục Trưởng phòng AI + Ban GĐ — chứng minh full-stack, scale đa kênh, auto-reply, ROI số học.  
**Audience:** TNT Group (E-commerce Đông Nam Á — PH, ID, MY).  
**Thời lượng trình diễn:** 12–15 phút (mở rộng từ DEMO_RUNBOOK 5 phút).

---

## 1. Tổng quan sản phẩm demo

### 1.1 Tên & narrative

**Tên demo:** *TNT AI CRM Command Center*  
**Câu chuyện 30 giây:**

> "Inbox Facebook, TikTok Shop, Shopee ngập tin Tagalog/Indo/Malay — CS nhập tay, bỏ lỡ đơn hủy. Em xây Command Center: một màn hình gửi tin thử, xem AI xử lý realtime, auto-reply tin thường, cảnh báo Leader tin khẩn, và widget ROI — tiết kiệm X triệu/tháng."

### 1.2 Kiến trúc tách BE / FE

```
┌─────────────────────────────────────────────────────────────────┐
│  crm-demo-ui (React/Vite)          crm-demo.nano.platform       │
│  - Multi-channel buttons           Traefik → nginx/static       │
│  - Live lead stream (SSE)                                       │
│  - Lead detail + auto-reply panel                               │
│  - Alert ticker + metrics cards                                 │
│  - ROI calculator widget                                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │ HTTPS (read + proxy ingest)
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  ai-crm-pipeline (BE — giữ nguyên tách service)                  │
│  crm-ingestion-api    webhook + /api/* + /api/events (SSE)       │
│  crm-ai-worker        Gemini extract + alerts + auto_reply      │
│  crm-demo-simulator   CLI/module gửi lead hàng loạt (optional)  │
└───────────────────────────┬─────────────────────────────────────┘
                            │
         Redis (queue + pub/sub)    PostgreSQL crm_db
```

| Layer | Folder | Container | RAM budget |
|-------|--------|-----------|------------|
| FE | `project_devops/apps/crm-demo-ui/` | `platform-crm-demo-ui` | 64M |
| Ingest + Read API | `ai-crm-pipeline/crm-ingestion-api/` | `platform-crm-ingestion` | 140M (+20M API) |
| AI Worker | `ai-crm-pipeline/crm-ai-worker/` | `platform-crm-worker` | 300M (+auto-reply) |
| Simulator | `ai-crm-pipeline/crm-demo-simulator/` | *(không bắt buộc container)* | — |

**Lý do tách FE:** deploy độc lập, Cursor task song song, demo UI không rebuild worker.

---

## 2. Map 5 ý tưởng → module cụ thể

| Ý tưởng | Module | Ưu tiên | Phụ thuộc |
|---------|--------|---------|------------|
| **1** Demo Dashboard UI | `crm-demo-ui` + Read API | P0 | 4.6 |
| **2** Lead Simulator | `crm-demo-simulator/lead_simulator.py` | P1 | API webhooks |
| **3** Auto-Reply | `crm-ai-worker/auto_reply.py` | P1 | DB columns, Gemini |
| **4** ROI Widget | `crm-demo-ui/src/roi/` | P2 | metrics API (optional) |
| **5** Multi-Channel | `/webhook/shopee` + UI buttons | P0 | ingestion |

---

## 3. Backend — chi tiết từng hạng mục

### 3.1 Mở rộng `crm-ingestion-api`

#### 3.1.1 Webhook Shopee (Ý tưởng 5)

**Endpoint:** `POST /webhook/shopee`

**Body (chuẩn demo):**
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

**Thay đổi code:**
- `ALLOWED_CHANNELS` thêm `shopee`
- Route riêng hoặc generic handler nhận `order_id` (Pydantic field optional)
- Metric label `channel=shopee`

#### 3.1.2 Read API cho Dashboard (Ý tưởng 1, 4, 5)

Prefix: `/api/v1` — **chỉ đọc**, không block ingest.

| Method | Path | Mô tả |
|--------|------|--------|
| GET | `/api/v1/leads` | List: `?limit=50&channel=&urgency=&since=` |
| GET | `/api/v1/leads/{message_id}` | Chi tiết 1 lead + auto-reply |
| GET | `/api/v1/alerts` | Leads `alert_sent=true` 24h gần nhất |
| GET | `/api/v1/metrics/summary` | Aggregates cho cards (1h / 24h) |
| POST | `/api/v1/demo/send` | **Proxy ingest** — UI gọi 1 endpoint, body có `channel` + template id |
| GET | `/api/v1/events/stream` | **SSE** — subscribe Redis `crm:events:leads` |

**`POST /api/v1/demo/send` body:**
```json
{
  "template_id": "cancel_angry_tl",
  "channel": "facebook",
  "overrides": { "message_id": "optional-uuid" }
}
```

Server map `template_id` → `raw_text` + metadata (xem `crm-demo-simulator/templates.json` dùng chung).

**CORS:** cho phép origin `https://crm-demo.nano.platform` (và `http://localhost:5173` dev).

**Auth demo:** header `X-Demo-Key` = env `CRM_DEMO_API_KEY` (optional lab); production demo tắt nếu empty.

#### 3.1.3 Realtime — Redis Pub/Sub (Ý tưởng 1)

**Khi worker persist lead xong:**
```python
await redis.publish("crm:events:leads", json.dumps({
  "type": "lead_processed",
  "message_id": "...",
  "channel": "shopee",
  "urgency": "high",
  "sentiment": "negative",
  "intent": "complaint",
  "alert_sent": true,
  "auto_reply_sent": false,
  "summary": "...",
  "processed_at": "..."
}))
```

**SSE handler (`/api/v1/events/stream`):**
- Client `EventSource` → server `GET` giữ connection
- Loop: `redis.subscribe("crm:events:leads")` → format `data: {...}\n\n`
- Heartbeat mỗi 15s: `: ping\n\n`

**Fallback UI:** polling `GET /api/v1/leads?since=` mỗi 3s nếu SSE lỗi.

---

### 3.2 Mở rộng `crm-ai-worker`

#### 3.2.1 Auto-Reply (Ý tưởng 3)

**File mới:** `crm-ai-worker/src/auto_reply.py`

**Luồng sau `persist_lead`:**
```
if should_auto_reply(extracted):
    reply = await generate_reply_gemini(raw_text, extracted, channel)
    UPDATE leads SET auto_reply_sent=true, auto_reply_content=reply, auto_reply_at=now()
    publish event type=auto_reply_sent
else:
    skip (alert-only path cho critical)
```

**`should_auto_reply` rules (demo — đơn giản, deterministic):**

| intent | urgency | Auto-reply? |
|--------|---------|-------------|
| inquiry, purchase | low, medium | ✅ |
| other + positive sentiment | low, medium | ✅ |
| cancel_order, complaint | high, critical | ❌ (alert Leader) |
| negative + high urgency | any | ❌ |

**Prompt Gemini (reply):**
```
You are TNT Shop CS bot. Reply in customer's language (tl/id/ms/en).
Tone: friendly, short, max 2 sentences. Include product hint if inquiry.
Intent: {intent}. Product: {product_interest}. Message: {raw_text}
Output plain text only, no JSON.
```

**Env:** `AUTO_REPLY_ENABLED=true` (default true in lab).

#### 3.2.2 Publish events

Trong `worker.py` sau INSERT thành công → gọi `publish_lead_event(redis, lead_row)`.

---

### 3.3 `crm-demo-simulator` (Ý tưởng 2)

**Path:** `ai-crm-pipeline/crm-demo-simulator/`

```
crm-demo-simulator/
├── lead_simulator.py      # CLI entry
├── templates.json         # 60–80 mẫu đa ngôn ngữ
├── channels.py            # facebook | tiktok | shopee | generic
├── requirements.txt       # httpx, click
└── README.md
```

**CLI:**
```bash
python lead_simulator.py \
  --base-url https://crm-ingest.nano.platform \
  --rate 2 \
  --duration 120 \
  --channels facebook,tiktok,shopee \
  --locale-mix tl,id,ms
```

**`templates.json` cấu trúc:**
```json
{
  "id": "price_inquiry_id",
  "channel": "tiktok",
  "locale": "id-ID",
  "raw_text": "Ka mau tanya harga serum vitamin C untuk kulit berminyak",
  "weight": 10,
  "category": "inquiry",
  "product_vertical": "cosmetics"
}
```

**Categories bắt buộc (TNT verticals):**
- `fashion` — size, return, OOTD praise
- `cosmetics` — harga, ingredients, allergy
- `home` — shipping delay, assembly
- `cancel_order` — angry TL/ID
- `complaint` — defective, wrong item
- `praise` — review khen

**Rate control:** asyncio hoặc sleep `1/rate` giữa request; `--burst 10` gửi 10 song song 1 lần.

**UI integration:** Dashboard nút "Start Simulator" → `POST /api/v1/demo/simulator/start` (optional Phase 4.2b) hoặc presenter chạy CLI song song.

---

### 3.4 Database migrations (Ý tưởng 3, 1)

**File:** `project_devops/platform/config/postgres/init/05-crm-demo-migration.sh`

**ALTER `leads`:**
```sql
ALTER TABLE leads ADD COLUMN IF NOT EXISTS auto_reply_sent BOOLEAN DEFAULT false;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS auto_reply_content TEXT NULL;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS auto_reply_at TIMESTAMPTZ NULL;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS order_id VARCHAR(64) NULL;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS shop_id VARCHAR(128) NULL;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS locale VARCHAR(16) NULL;
```

**Index:** `idx_leads_channel_processed` ON (channel, processed_at DESC).

Cập nhật `DATA_MODEL.md` + worker INSERT list columns.

---

## 4. Frontend — `crm-demo-ui`

### 4.1 Tech stack

| Chọn | Lý do |
|------|--------|
| React 18 + Vite 5 | Nhanh scaffold, HMR khi dev |
| TypeScript | Type-safe API client |
| Tailwind CSS 3 | UI chuyên nghiệp trong 1–2 ngày |
| TanStack Query | Cache leads list |
| EventSource API | SSE native |
| Recharts | ROI bar/line (Ý tưởng 4) |

**Không dùng** Next.js (overkill cho static demo trên Traefik).

### 4.2 Layout màn hình (single-page Command Center)

```
┌──────────────────────────────────────────────────────────────────┐
│  TNT AI CRM Command Center          🟢 Live  │ Queue: 3 │ 1.2k/min │
├──────────────┬───────────────────────────────────────────────────┤
│  CHANNELS    │  LIVE LEAD STREAM (SSE)                            │
│  [Facebook]  │  ┌─────┬────────┬─────────┬────────┬──────────┐   │
│  [TikTok]    │  │ ch  │ intent │ urgency │ sent.  │ time     │   │
│  [Shopee]    │  └─────┴────────┴─────────┴────────┴──────────┘   │
│  [Generic]   │  (rows animate in, critical = red border)          │
│              ├───────────────────────────────────────────────────┤
│  SIMULATOR   │  LEAD DETAIL (click row)                           │
│  Rate: [2/s] │  Raw text │ AI summary │ sentiment │ intent        │
│  [▶ Start]   │  Auto-reply bubble (if sent)                       │
│  [■ Stop]    ├───────────────────────────────────────────────────┤
│              │  ALERTS TICKER │ METRICS CARDS                     │
│  ROI WIDGET  │  🚨 3 critical │ Processed: 847 │ Avg LLM: 4.2s   │
│  CS staff:12 │  [chart ingest vs processed]                       │
│  Salary: ... │                                                    │
└──────────────┴───────────────────────────────────────────────────┘
```

### 4.3 Các màn hình / component

| Component | Ý tưởng | Hành vi |
|-----------|---------|---------|
| `ChannelButtons` | 5 | Click → `POST /api/v1/demo/send` với template ngẫu nhiên theo channel |
| `LeadStream` | 1 | SSE → prepend row; sound optional off |
| `LeadDetail` | 1, 3 | Panel phải; hiện `auto_reply_content` |
| `AlertTicker` | 1 | Filter `alert_sent`; flash animation |
| `MetricsBar` | 1 | `GET /api/v1/metrics/summary` refresh 10s |
| `SimulatorPanel` | 2 | Gọi CLI qua API hoặc hiển thị hướng dẫn + link |
| `RoiCalculator` | 4 | Pure client math + Recharts |

### 4.4 ROI Calculator logic (Ý tưởng 4)

**Inputs (slider/input):**
- `cs_staff_count` (default 25)
- `avg_salary_usd` (default 450)
- `messages_per_day` (default 8000)
- `auto_reply_rate` (default 0.65) — % tin thường AI trả
- `avg_response_before_min` (default 45)
- `avg_response_after_min` (default 2)

**Outputs:**
```text
monthly_savings = cs_staff_count * avg_salary_usd * auto_reply_rate * 0.6
hours_saved = messages_per_day * auto_reply_rate * 2min / 60
cancel_reduction_pct = 15% (assumption label)
annual_roi = monthly_savings * 12
```

**Hiển thị disclaimer:** *"Mô hình giả định cho demo — tinh chỉnh theo số liệu TNT thực tế."*

### 4.5 Env FE (build-time)

```env
VITE_CRM_API_BASE=https://crm-ingest.nano.platform
VITE_SSE_URL=https://crm-ingest.nano.platform/api/v1/events/stream
VITE_DEMO_KEY=optional
```

**Dockerfile:** multi-stage `node:20-alpine` build → `nginx:alpine` serve `dist/`.

---

## 5. Platform & Vagrant integration

### 5.1 Compose (`docker-compose.apps.yml`)

**Service mới:**
```yaml
crm-demo-ui:
  build:
    context: ../../apps/crm-demo-ui
  container_name: platform-crm-demo-ui
  networks: [platform-network]
  labels:
    - traefik.http.routers.crm-demo.rule=Host(`crm-demo.nano.platform`)
    - traefik.http.routers.crm-demo.entrypoints=web,websecure
    - traefik.http.routers.crm-demo.tls=true
  deploy:
    resources:
      limits: { memory: 64M }
```

**crm-ingestion-api:** tăng memory limit 120M → 140M; env `CRM_DEMO_API_KEY`, `CORS_ORIGINS`.

### 5.2 Vagrantfile (đã bổ sung)

Hosts nội bộ VM + hướng dẫn presenter:
- `crm-demo.nano.platform` — Command Center
- `crm-ingest.nano.platform` — API (FE gọi trực tiếp hoặc qua proxy)

`post_up_message` liệt kê URL demo Phase 4.

### 5.3 Presenter hosts file (Windows)

```
<VM_IP> crm-demo.nano.platform
<VM_IP> crm-ingest.nano.platform
<VM_IP> grafana.nano.platform
```

---

## 6. Kịch bản demo 15 phút (thay curl)

| Phút | Hành động | Nói |
|------|-----------|-----|
| 0–2 | Mở `https://crm-demo.nano.platform` | Pain TNT, 3 kênh, đa ngôn ngữ |
| 2–4 | Bấm **Shopee** → tin MY hỏi giao hàng | Ingest < 1s, stream hiện row |
| 4–6 | Bấm **Facebook** → cancel angry TL | Alert ticker đỏ, Telegram (phone) |
| 6–8 | Bấm **TikTok** → hỏi giá cosmetics ID | Auto-reply bubble hiện sau ~5s |
| 8–10 | **Start Simulator** 5 lead/s | Stream đầy, metrics tăng |
| 10–12 | Mở **ROI widget** — chỉnh 25 CS → savings | "Tiết kiệm ~$X/tháng" |
| 12–14 | Grafana tab — queue depth, LLM latency | Vận hành production-ready |
| 14–15 | Q&A | Scale ID/MY, thêm kênh mới = 1 webhook |

---

## 7. Thứ tự thực thi cho Cursor (sprint)

### Sprint A — P0 (demo tối thiểu chạy được)

1. **4.6a** DB migration `05-crm-demo-migration.sh`
2. **4.5** `/webhook/shopee` + channel shopee
3. **4.6b** Read API `/api/v1/leads`, `/metrics/summary`, `/demo/send`
4. **4.6c** Redis publish từ worker + SSE endpoint
5. **4.1** Scaffold `crm-demo-ui` + ChannelButtons + LeadStream + compose Traefik
6. **4.7** Vagrant hosts + smoke `smoke-test-crm-demo.sh`

### Sprint B — P1 (wow factor)

7. **4.3** `auto_reply.py` + UI hiển thị reply
8. **4.2** `lead_simulator.py` + `templates.json` (60 mẫu)
9. **4.1b** AlertTicker + LeadDetail + MetricsBar

### Sprint C — P2 (đóng deal IT)

10. **4.4** RoiCalculator + charts
11. **4.2b** Simulator API start/stop (optional)
12. **4.10** Cập nhật DEMO_RUNBOOK v2 + PHASE4_VALIDATION.md

---

## 8. Tiêu chí "DONE" — demo đỗ Trưởng phòng AI

- [ ] Presenter **không gõ curl** trong buổi demo chính
- [ ] 3 nút kênh + stream realtime < 2s latency hiển thị (sau worker xong)
- [ ] Auto-reply hiển thị cho tin inquiry (EN/ID/TL/MY)
- [ ] Alert critical lên Telegram + ticker đỏ
- [ ] Simulator 2 lead/s trong 60s không 503 queue
- [ ] ROI widget tính savings với số người thật TNT đưa vào
- [ ] `vagrant provision` + `./cli.sh up` — 2 URL HTTPS xanh
- [ ] Grafana CRM dashboard vẫn hoạt động song song

---

## 9. Rủi ro & giảm thiểu

| Rủi ro | Giảm thiểu |
|--------|------------|
| Gemini rate limit khi simulator 10/s | Default 2/s; queue backpressure 503 có message UI |
| RAM 6GB VM | FE 64M; tắt Odoo; worker 300M cap |
| SSE disconnect | UI fallback polling |
| CORS / TLS | Traefik cùng domain wildcard `*.nano.platform` |
| Demo key lộ | Chỉ lab; empty = no auth |

---

## 10. Tài liệu phải cập nhật khi implement

- [API_CONTRACT.md](./API_CONTRACT.md) — §8 Read API, §9 Shopee
- [DATA_MODEL.md](./DATA_MODEL.md) — auto_reply columns
- [ARCHITECTURE.md](../ARCHITECTURE.md) — diagram thêm FE + SSE
- [DEMO_RUNBOOK.md](./DEMO_RUNBOOK.md) — kịch bản 15 phút UI
- [IMPLEMENTATION_CHECKLIST.md](./IMPLEMENTATION_CHECKLIST.md) — link Phase 4
- [DEMO_PLATFORM_CHECKLIST.md](./DEMO_PLATFORM_CHECKLIST.md) — task Cursor
- `ai-system/MASTER_PLAN.md` — Phase 4 table
- `Vagrantfile` — hosts + post_up_message

---

*Phase 4 — bản kế hoạch authority cho Cursor autonomous implementation.*
