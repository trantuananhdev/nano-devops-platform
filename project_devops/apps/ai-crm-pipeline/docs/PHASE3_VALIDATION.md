# Phase 3 Validation — AI-Driven CRM Pipeline

**Status**: Implementation complete (pending lab VM run)  
**Date**: 2026-05-25

---

## Deliverables checklist

| Task | Deliverable | Status |
|------|-------------|--------|
| 3.1 | Design docs | ✅ |
| 3.2 | `crm-ingestion-api/` | ✅ |
| 3.3 | `crm-ai-worker/` | ✅ |
| 3.4 | `04-crm-init.sh` | ✅ |
| 3.5 | `alerts.py` integrated | ✅ |
| 3.6 | `docker-compose.apps.yml` | ✅ |
| 3.7 | CI path filters + build context | ✅ |
| 3.8 | Grafana `crm-pipeline.json` | ✅ |
| 3.9 | `smoke-test-crm-ingestion.sh` | ✅ |
| 3.10 | This document | ✅ |

---

## Lab validation (on VM)

```bash
vagrant ssh
./cli.sh up
bash project_devops/platform/ops/smoke-tests/smoke-test-crm-ingestion.sh
```

Keys live in repo root `.env` (`LLM_PROVIDER`, `GEMINI_API_KEY`, optional `TELEGRAM_*`).  
`./cli.sh up` loads them automatically — no `export` needed.

Send hot lead:
```bash
curl -sk -X POST https://crm-ingest.nano.platform/webhook/facebook \
  -H "Content-Type: application/json" \
  -d '{"message_id":"validate-cancel-1","raw_text":"Cancel order NOW!!!","channel":"facebook"}'
```

Verify DB:
```bash
docker exec -it platform-postgres psql -U crm_user -d crm_db \
  -c "SELECT message_id, urgency, intent, alert_sent FROM leads ORDER BY processed_at DESC LIMIT 5;"
```

---

## Docker Hub 429 (rate limit)

Provisioning runs `docker_registry_login.sh` automatically:

- Reads repo root `.env` → `GITHUB_TOKEN` (same as ai-agent / `BOOTSTRAP_REPO_FULL_NAME`)
- `docker login ghcr.io` as repo owner (e.g. `trantuananhdev`)
- Registry mirror `mirror.gcr.io` in `/etc/docker/daemon.json`
- Pre-pull `python:3.11-alpine`, `node:20-slim`, …

Re-run after `vagrant provision` or: `sudo sh .../docker_registry_login.sh` then `sudo rc-service nano-platform restart`.

## Known limitations (demo scope)

- Docker build not verified on Windows dev host (no Docker CLI)
- Fresh Postgres volume required for `04-crm-init.sh` (or manual run)
- Gemini API key mandatory for worker processing

---

## Interview readiness

Follow [DEMO_RUNBOOK.md](./DEMO_RUNBOOK.md) after lab validation passes.
