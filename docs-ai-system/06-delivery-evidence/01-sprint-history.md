# Sprint History — T-01 đến T-66

> **Audience:** CEO, Project Stakeholder
> **Mục đích:** Chứng minh delivery capability — mỗi task = 1 deliverable có acceptance criteria và verify command.

---

## Sprint 1 — 10 ngày (Foundation)

| Task | Deliverable | Status |
|------|-------------|--------|
| T-01 | FastAPI skeleton + Docker Compose + `/health` endpoint | ✅ DONE |
| T-02 | Ansible deploy Ubuntu LLM node (llama-server :8080) | ✅ DONE |
| T-03 | DB models + 12 tables + Alembic migrations | ✅ DONE |
| T-04 | Celery ReAct agent + ai_audit_logs mọi tool call | ✅ DONE |
| T-05 | WebSocket real-time: started/completed events | ✅ DONE |
| T-06 | Frontend core: DossierList, Workspace, Admin, Alerts | ✅ DONE |
| T-07 | 5+ tool mocks (ERP, Legal, OCR) via Gemini | ✅ DONE |
| T-08 | Chroma seed + LegalGraphRAG (tra cứu pháp luật) | ✅ DONE |
| T-09 | CI pipeline GitHub Actions + HDTV_DEMO_RUNBOOK.md | ✅ DONE |
| T-10 | 8 FE views wired: Dashboard, Chat, Workflow, Graph, Schedule, Skills, Tools, Settings | ✅ DONE |

---

## Phase 8 — Agent Level 4 (T-11 → T-24)

| Task | Deliverable | Status |
|------|-------------|--------|
| T-11 | Meilisearch full-text search + Ctrl+K modal + graceful degraded | ✅ DONE |
| T-12 | BPMN workflow persistence (GET/PUT + audit log) | ✅ DONE |
| T-13 | Dossier Create + PDF Upload to MinIO (3-step wizard) | ✅ DONE |
| T-14 | Admin panel wire + PDF viewer + Meilisearch sync | ✅ DONE |
| T-15 | Vector Memory (Chroma HTTP client + degraded fallback) | ✅ DONE |
| T-16 | Cross-dossier Memory + User Preferences per role | ✅ DONE |
| T-17 | Plan-Execute-Reflect Orchestrator (WS: plan_created, plan_revised) | ✅ DONE |
| T-18 | Parallel Tool Executor (asyncio.gather by parallel_group) | ✅ DONE |
| T-19 | Critic Module (approved/needs_revision + WS: critic_review) | ✅ DONE |
| T-20 | Feedback API + Learning Loop (upsert to Chroma feedback-lessons) | ✅ DONE |
| T-21 | Tool Chaining: EcoOcrExtract → LegalGraphRAG (output_mapping) | ✅ DONE |
| T-22 | Human-in-the-Loop: pause/resume + clarification modal | ✅ DONE |
| T-23 | Role-Based Agent Profiles (4 roles: leader, dept_head, admin, specialist) | ✅ DONE |
| T-24 | Agent Intelligence Dashboard (4 KPI: revision_rate, rejection_rate, feedback, memory) | ✅ DONE |

---

## Phase 9 — Infrastructure (T-25 → T-30)

| Task | Deliverable | Status |
|------|-------------|--------|
| T-25 | LLM Circuit Breaker (CLOSED/OPEN/HALF_OPEN) + Gemini key rotation cooldown | ✅ DONE |
| T-26 | Docker Sandbox Executor + AiAuditLog cho mọi sandbox execution | ✅ DONE |
| T-27 | RAG Ingestion Pipeline (Celery beat: ingest mỗi 6h, cleanup 30 ngày) | ✅ DONE |
| T-28 | Observability LLMOps: 14 alert rules + Grafana 5-panel dashboard + OTel tracing | ✅ DONE |
| T-29 | MCP SSE Streaming + Tool Output Schema Validation | ✅ DONE |
| T-30 | Execution Harness: validation + per-tool timeout + retry + audit correlation | ✅ DONE |

---

## Phase 10 — Operations (T-31 → T-37)

| Task | Deliverable | Status |
|------|-------------|--------|
| T-31 | LLM Node: Caddy + node-exporter + Promtail (Ansible role) | ✅ DONE |
| T-32 | Observability complete: Alertmanager + HDTV alert rules | ✅ DONE |
| T-33 | API Keys Management Dashboard (bcrypt hashing, CRUD, copy UI) | ✅ DONE |
| T-34 | HDTV Workflow Grafana Dashboard | ✅ DONE |
| T-35 | Backup Strategy: PostgreSQL + MinIO + Chroma automated | ✅ DONE |
| T-36 | MCP Token Management + Audit Logs UI tab | ✅ DONE |
| T-37 | Ansible LLM Node Teardown + Reset playbook | ✅ DONE |

---

## Phase 11-15 — Hardening (T-38 → T-66)

| Phase | Tasks | Deliverables | Status |
|-------|-------|-------------|--------|
| 11 | T-38→T-41 | Virtual Scroll, Lazy Load, Pagination, rAF UI | ✅ DONE |
| 12 | T-42→T-46 | Ansible inventory fix, Smoke Tests, .env validation | ✅ DONE |
| 13 | T-47→T-50 | SSH Bootstrap hardening, ansible-runner fix | ✅ DONE |
| 14 | T-51→T-52 | Root-Key workflow simplification (remove complexity) | ✅ DONE |
| 15 | T-53→T-66 | DB migration robustness (DuplicateObjectError fix) | ✅ DONE |

---

## Velocity Summary

```
Sprint 1 (10 days):    10 tasks — 1 task/day
Phase 8  (ongoing):    10 tasks — Agent Level 4
Phase 9  (ongoing):     6 tasks — Infrastructure
Phase 10 (ongoing):     7 tasks — Operations
Phase 11 (ongoing):     4 tasks — Performance
Phase 12 (ongoing):     5 tasks — Hardening
Phase 13 (ongoing):     4 tasks — Infra fixes
Phase 14 (ongoing):     2 tasks — Simplification
Phase 15 (ongoing):    14 tasks — Migration fixes
────────────────────────────────
TOTAL:                 66 tasks — ALL DONE ✅
```
