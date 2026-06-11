# AI Context Snapshot

**Last Updated**: 2026-05-25 (geminiProvider.py parity; VM validation pending)

## Phase & State
- **Current Phase**: Phase 3 — AI-Driven CRM (~90%)
- **Implementation**: ✅ crm-ingestion-api, crm-ai-worker, compose, CI, Grafana, smoke script
- **Active Task**: Lab validation on Vagrant VM

## LLM layer (aligned with ai-agent)
- `crm-ai-worker/src/geminiProvider.py` ← port of `ai-agent/src/llm/geminiProvider.js`
- `crm-ai-worker/src/providerFactory.py` ← port of `providerFactory.js`

## Services added
| Service | Container | URL |
|---------|-----------|-----|
| crm-ingestion-api | platform-crm-ingestion | https://crm-ingest.nano.platform |
| crm-ai-worker | platform-crm-worker | metrics :9100 internal |

## User note
- User is software engineer (not expert) — autonomous agent continues; user runs demo on VM.

## Next action
- `vagrant ssh` → validate per PHASE3_VALIDATION.md

## Blockers
- Docker unavailable on Windows host — VM only for runtime test
