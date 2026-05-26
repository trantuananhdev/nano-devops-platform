# Phase 4 Validation — TNT AI CRM Command Center

**Status:** Lab smoke + E2E passed on Vagrant VM (2026-05-26)  
**Date:** 2026-05-25 (updated 2026-05-26)

---

## Deliverables checklist

| Task | Deliverable | Code | Lab |
|------|-------------|------|-----|
| 4.0 | DEMO_PLATFORM_PLAN + checklist | ✅ | — |
| 4.1 | `05-crm-demo-migration.sh` + DATA_MODEL | ✅ | ✅ smoke |
| 4.2 | Shopee webhook | ✅ | ✅ smoke |
| 4.3 | Read API + `/demo/send` | ✅ | ✅ smoke |
| 4.4 | SSE + Redis pub/sub | ✅ | ✅ (UI polling fallback OK) |
| 4.5 | `auto_reply.py` | ✅ | ✅ (static fallback khi Gemini 429) |
| 4.6 | `lead_simulator.py` + 60 templates | ✅ | ✅ burst smoke |
| 4.7 | `crm-demo-ui` React | ✅ | ✅ HTTPS |
| 4.8 | compose + Traefik + smoke | ✅ | ✅ |
| 4.9 | Grafana v2 + DEMO_RUNBOOK v2 | ✅ | ⏳ presenter rehearsal |
| 4.10 | PROJECT_STATE + MASTER_PLAN | ✅ | — |

---

## Lab validation procedure

```bash
vagrant ssh
cd /workspace   # DEV mode, or /opt/platform/src/nano-project-devops
./cli.sh up
```

### Smoke

```bash
bash project_devops/platform/ops/smoke-tests/smoke-test-crm-ingestion.sh
bash project_devops/platform/ops/smoke-tests/smoke-test-crm-demo.sh
bash project_devops/platform/ops/smoke-tests/smoke-test-crm-e2e.sh
bash project_devops/platform/ops/smoke-tests/smoke-test-crm-burst.sh
```

### Schema (Phase 4 columns)

```bash
docker exec platform-postgres psql -U crm_user -d crm_db -c '\d leads'
# Expect: auto_reply_sent, auto_reply_content, order_id, shop_id, locale
```

### UI rehearsal (presenter)

1. `https://crm-demo.nano.platform` — Command Center loads
2. Shopee → stream row
3. Facebook cancel → alert ticker (+ Telegram)
4. TikTok inquiry → auto-reply in detail panel
5. Grafana **CRM AI Pipeline** — auto-reply + leads by channel panels
6. `smoke-test-observability.sh` — Grafana + Prometheus HTTPS green

### Simulator load

```bash
cd project_devops/apps/ai-crm-pipeline/crm-demo-simulator
pip install -r requirements.txt
python lead_simulator.py --base-url https://crm-ingest.nano.platform --rate 2 --duration 30
```

Expect: no sustained `503`; queue depth recovers on Grafana.

---

## Services & URLs

| Service | Host | Notes |
|---------|------|-------|
| Demo UI | `crm-demo.nano.platform` | nginx static, Traefik TLS |
| Ingest + API | `crm-ingest.nano.platform` | webhooks + `/api/v1/*` + SSE |
| Worker | internal | metrics `:9100` |
| Grafana | `grafana.nano.platform` | dashboard uid `crm-pipeline-demo` |

---

## Environment

| Variable | Purpose |
|----------|---------|
| `GEMINI_API_KEY` | Worker LLM + auto-reply |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | Leader alerts |
| `AUTO_REPLY_ENABLED` | default `true` in compose |
| `CRM_DEMO_API_KEY` | optional lab auth for Read API |
| `CORS_ORIGINS` | includes `crm-demo.nano.platform` |

---

## Known limitations

- Docker build not verified on Windows host without Docker CLI
- Fresh Postgres volume needed for `05-crm-demo-migration.sh` on existing DB (manual ALTER or recreate volume)
- Gemini rate limit under simulator >5/s — use 2/s default; worker có `CRM_DEMO_LLM_FALLBACK` + retry 429
- Worker không block queue khi retry (requeue async); `CRM_WORKER_JOB_DELAY_MS` default 1200ms
- SSE may fall back to polling on strict corporate proxies
- `COPY_PROJECT_DEVOPS=1`: sau sửa code chạy `vagrant provision` rồi rebuild CRM services trên VM

---

## Interview readiness

Follow [DEMO_RUNBOOK.md](./DEMO_RUNBOOK.md) (Phase 4 UI script).  
Phase 3 curl path remains valid for engineering debug only.
