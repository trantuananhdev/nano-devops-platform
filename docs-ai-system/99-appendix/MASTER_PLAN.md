# MASTER_PLAN — EVN HDTV (10 ngày thử việc)

## Definition of Done

- [x] Topology 2 máy: Ubuntu LLM + Alpine app
- [x] ReAct agent async via Celery
- [x] ai_audit_logs mọi tool call
- [x] WebSocket real-time appraisal
- [x] FE wire 4 views core
- [x] Gemini Flash tool mocks
- [x] Chroma GraphRAG seed
- [x] CI build hdtv-ai-platform
- [x] HDTV_DEMO_RUNBOOK.md

## Day-by-Day

| Day | Focus |
|-----|-------|
| D1 | ai-system docs + FastAPI skeleton + compose |
| D2 | Ansible llm_node + llm_client |
| D3 | DB models + seed |
| D4 | Celery ReAct + audit |
| D5 | WebSocket + risk scoring |
| D6 | FE Pinia wire |
| D7 | Tool mocks |
| D8 | Chroma RAG |
| D9 | Admin/Alerts + test.sh |
| D10 | Demo runbook + rehearsal |

## Strategic Value (JD proof)

| Stakeholder | Demo moment |
|-------------|-------------|
| CEO | Risk HIGH alert on budget exceed |
| CTO | ai_audit_logs JSON + async 202 |
| Architect | LLM separated, swap model without redeploy app |
| DevOps | vagrant up → ansible-deploy-llm → hdtv-up |
