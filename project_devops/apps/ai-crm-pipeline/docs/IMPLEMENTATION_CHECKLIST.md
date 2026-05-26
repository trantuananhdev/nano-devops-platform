# Implementation Checklist — Phase 3 (Cursor Autonomous)

> Mỗi section = **một** `ACTIVE_TASK`. Đánh dấu `[x]` trong EXECUTION_HISTORY khi xong.  
> Đọc [CURSOR_AUTONOMOUS_GUIDE.md](../CURSOR_AUTONOMOUS_GUIDE.md) trước mọi task.

---

## Task 3.1 — Design ✅

- [x] README.md
- [x] CURSOR_AUTONOMOUS_GUIDE.md
- [x] ARCHITECTURE.md
- [x] docs/API_CONTRACT.md
- [x] docs/DATA_MODEL.md
- [x] docs/ALERT_RULES.md
- [x] docs/DEMO_RUNBOOK.md
- [x] docs/IMPLEMENTATION_CHECKLIST.md

---

## Task 3.2 — crm-ingestion-api ✅

**ACTIVE_TASK objective:** FastAPI async webhook + Redis enqueue.

### Files to create
- [x] `crm-ingestion-api/src/main.py`
- [x] `crm-ingestion-api/src/config.py`
- [x] `crm-ingestion-api/src/metrics.py`
- [x] `crm-ingestion-api/requirements.txt`
- [x] `crm-ingestion-api/Dockerfile`

### Requirements
- [x] Endpoints per API_CONTRACT.md
- [x] Dedup Redis keys per DATA_MODEL.md
- [x] Prometheus metrics per ARCHITECTURE.md
- [x] Non-root user in Dockerfile (copy health-api pattern)

### DONE WHEN
- [x] `docker build` succeeds locally
- [ ] Unit: POST generic → 200 + Redis LLEN increases (manual or pytest optional) — after Task 3.6 compose

### State update
- [x] EXECUTION_HISTORY entry
- [x] ACTIVE_TASK → 3.3

---

## Task 3.3 — crm-ai-worker ✅

### Files to create
- [x] `crm-ai-worker/src/worker.py`
- [x] `crm-ai-worker/src/llm_gemini.py`
- [x] `crm-ai-worker/src/alerts.py`
- [x] `crm-ai-worker/requirements.txt`
- [x] `crm-ai-worker/Dockerfile`

### Requirements
- [ ] BRPOP loop, Gemini JSON, validate enums
- [ ] INSERT `leads` + `processing_log`
- [ ] DLQ after 3 failures
- [ ] Metrics: queue_depth, llm_latency, jobs_processed

### DONE WHEN
- [ ] Process one queued job end-to-end (Gemini key required)

---

## Task 3.4 — PostgreSQL init ✅

### Files
- [x] `project_devops/platform/config/postgres/init/04-crm-init.sh`
- [ ] Secret template note in platform secrets README (if exists)

### DONE WHEN
- [ ] Fresh `docker compose up` creates `crm_db` + tables

---

## Task 3.5 — Alerts ✅

### Files
- [x] Complete `crm-ai-worker/src/alerts.py` per ALERT_RULES.md

### DONE WHEN
- [ ] Demo cancel message triggers Telegram (test chat)

---

## Task 3.6 — Platform wiring ✅

### Files
- [x] `docker-compose.apps.yml` — services `crm-ingestion-api`, `crm-ai-worker`
- [ ] Secrets entries in compose `secrets:` block

### Labels
- [ ] Traefik host `crm-ingest.nano.platform`
- [ ] `prometheus.scrape=true` port 8080

### DONE WHEN
- [ ] `./cli.sh up` — both containers healthy

---

## Task 3.7 — CI/CD ✅

### Files
- [x] `.github/workflows/ci.yml` — path filters + build matrix entries

### DONE WHEN
- [ ] PR touching `crm-ingestion-api/**` triggers build

---

## Task 3.8 — Observability ✅

### Files
- [x] `monitoring/grafana/dashboards/crm-pipeline.json`
- [ ] Alert rules in `config/prometheus/alerts/` (optional platform-alerts.yml section)

### DONE WHEN
- [ ] Dashboard shows ingest rate, queue depth, LLM latency, alerts sent

---

## Task 3.9 — Smoke + demo validation ✅

### Files
- [x] `platform/ops/smoke-tests/smoke-test-crm-ingestion.sh`

### DONE WHEN
- [ ] Script passes on lab VM
- [ ] DEMO_RUNBOOK.md steps verified

---

## Task 3.10 — Phase closure ✅

### Files
- [x] `docs/PHASE3_VALIDATION.md`
- [ ] Update `ai-system/PROJECT_STATE.md` Phase 3 = complete
- [ ] Update `ai-system/MASTER_PLAN.md` task statuses

---

## Golden path cross-reference

| Step | Golden path | CRM task |
|------|-------------|----------|
| Scaffold | §2 | 3.2, 3.3 |
| Integrate | §4 | 3.6, 3.7 |
| Test | §5 | 3.9 |
| Document | §6 | 3.10 |

**Compose path thực tế:** `project_devops/platform/composition/docker-compose.apps.yml` (không phải root docker-compose.yml).

---

## Phase 4 — Demo Platform (see DEMO_PLATFORM_CHECKLIST.md)

| Task | Status |
|------|--------|
| 4.1–4.10 code + docs | ✅ |
| 4.lab VM + UI rehearsal | ⏳ [PHASE4_VALIDATION.md](./PHASE4_VALIDATION.md) |

Presenter runbook: [DEMO_RUNBOOK.md](./DEMO_RUNBOOK.md) (UI, 12–15 min).
