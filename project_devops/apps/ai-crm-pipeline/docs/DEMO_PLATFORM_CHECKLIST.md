# Demo Platform Checklist — Phase 4 (Cursor Autonomous)

> **Authority:** [DEMO_PLATFORM_PLAN.md](./DEMO_PLATFORM_PLAN.md)  
> Mỗi task = một `ACTIVE_TASK` trong `ai-system/`. Đánh dấu `[x]` khi xong.

---

## Task 4.0 — Planning ✅

- [x] DEMO_PLATFORM_PLAN.md
- [x] DEMO_PLATFORM_CHECKLIST.md
- [x] ai-system/AI_BOOT.md (Phase 4 pointers)
- [x] Vagrantfile hosts `crm-demo.nano.platform`

---

## Task 4.1 — DB migration + DATA_MODEL ✅

**Objective:** Schema hỗ trợ auto-reply, Shopee fields.

### Files
- [x] `platform/config/postgres/init/05-crm-demo-migration.sh`
- [x] Update `docs/DATA_MODEL.md` (columns + sample queries)

### DONE WHEN
- [ ] `docker exec platform-postgres psql -U crm_user -d crm_db -c '\d leads'` shows new columns (lab VM)

---

## Task 4.2 — Shopee webhook (Ý tưởng 5) ✅

**Objective:** `POST /webhook/shopee` + tests.

### Files
- [x] `crm-ingestion-api/src/main.py` — route, `order_id` field
- [x] `docs/API_CONTRACT.md` — § Shopee

### DONE WHEN
- [ ] curl Shopee body → 200 accepted (lab VM)
- [ ] Metric `crm_ingest_requests_total{channel="shopee"}` increments

---

## Task 4.3 — Read API + demo send proxy ✅

**Objective:** Dashboard không gọi webhook trực tiếp từ browser (CORS/key).

### Files
- [x] `crm-ingestion-api/src/api_read.py`
- [x] `crm-ingestion-api/src/demo_templates.py`
- [x] `crm-demo-simulator/templates.json`
- [x] `docs/API_CONTRACT.md` — § Read API

### Endpoints
- [x] `GET /api/v1/leads`
- [x] `GET /api/v1/leads/{message_id}`
- [x] `GET /api/v1/alerts`
- [x] `GET /api/v1/metrics/summary`
- [x] `POST /api/v1/demo/send`

### DONE WHEN
- [ ] Postman/curl list returns JSON array after 1 demo message processed

---

## Task 4.4 — Realtime SSE (Ý tưởng 1) ✅

**Objective:** Worker publish + ingestion SSE.

### Files
- [x] `crm-ai-worker/src/events.py` — `publish_lead_event`
- [x] `crm-ingestion-api` — `GET /api/v1/events/stream`
- [x] Wire publish after persist + after auto_reply

### DONE WHEN
- [ ] `curl -N https://crm-ingest.../api/v1/events/stream` receives event after webhook

---

## Task 4.5 — Auto-reply worker (Ý tưởng 3) ✅

**Objective:** Gemini reply cho tin thường; skip critical.

### Files
- [x] `crm-ai-worker/src/auto_reply.py`
- [x] `crm-ai-worker/src/worker.py` — integrate
- [x] Env `AUTO_REPLY_ENABLED` in compose

### DONE WHEN
- [ ] Inquiry message → `auto_reply_sent=true` + content in DB
- [ ] Cancel angry → `auto_reply_sent=false`, `alert_sent=true`

---

## Task 4.6 — Lead simulator CLI (Ý tưởng 2) ✅

**Objective:** `lead_simulator.py --rate N`.

### Files
- [x] `crm-demo-simulator/lead_simulator.py`
- [x] `crm-demo-simulator/templates.json` (≥60 entries, tl/id/ms)
- [x] `crm-demo-simulator/README.md`

### DONE WHEN
- [ ] `--rate 2 --duration 30` sends 60 messages without 503
- [ ] Dashboard stream shows rows (manual run during demo)

---

## Task 4.7 — crm-demo-ui scaffold (Ý tưởng 1, 4, 5) ✅

**Objective:** React Command Center on Traefik.

### Files
- [x] `apps/crm-demo-ui/package.json`, `vite.config.ts`, `tailwind`
- [x] `src/App.tsx`, `ChannelButtons`, `LeadStream`, `LeadDetail`
- [x] `src/AlertTicker.tsx`, `src/MetricsBar.tsx`
- [x] `src/RoiCalculator.tsx` (Ý tưởng 4)
- [x] `Dockerfile`, `nginx.conf`
- [x] `docker-compose.apps.yml` service `crm-demo-ui`

### DONE WHEN
- [ ] `https://crm-demo.nano.platform` loads HTTPS
- [ ] Click Facebook → row appears in stream within 15s

---

## Task 4.8 — Platform wiring + Vagrant

### Files
- [x] `docker-compose.apps.yml` — crm-demo-ui, ingestion env CORS
- [x] `Vagrantfile` — verify hosts (done in 4.0)
- [x] `main_setup.sh` hosts loop — `crm-demo.nano.platform` present
- [x] `platform/ops/smoke-tests/smoke-test-crm-demo.sh`

### DONE WHEN
- [ ] `vagrant provision` + `./cli.sh up` — demo UI + ingest healthy (lab)

---

## Task 4.9 — Observability + docs ✅

### Files
- [x] Grafana panel: `auto_reply_total`, `leads_by_channel` (`crm-pipeline.json` v2)
- [x] `docs/DEMO_RUNBOOK.md` v2 (UI script 15 min)
- [x] `docs/PHASE4_VALIDATION.md`

### DONE WHEN
- [ ] Presenter rehearsal checklist all green (lab)

---

## Task 4.10 — Phase closure ✅

- [x] `ai-system/PROJECT_STATE.md` Phase 4 code complete
- [x] `ai-system/MASTER_PLAN.md` tasks checked
- [x] `README.md` link DEMO_PLATFORM_PLAN + PHASE4_VALIDATION

---

## Dependency graph

```
4.1 → 4.5
4.1 → 4.3
4.2 → 4.7 (Shopee button)
4.3 → 4.7
4.4 → 4.7 (stream)
4.5 → 4.7 (detail panel)
4.6 parallel after 4.2
4.7 → 4.8 → 4.9 → 4.10
```

**Cursor rule:** Không bắt đầu 4.7 cho đến khi 4.3 + 4.4 có stub hoạt động (mock SSE OK tạm).
