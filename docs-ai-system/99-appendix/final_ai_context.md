# Final AI Context — EVN HDTV Agentic Appraisal Platform

## Project

Agentic AI platform for EVNHANOI Board of Members (HĐTV) to appraise dossiers (Tờ trình).

## Topology (STRICT)

- **LLM Node (Ubuntu):** `llama-server` Gemma 4 E2B at `LLM_BASE_URL` — OpenAI-compatible `/v1/chat/completions`
- **App Node (Alpine VM):** FastAPI, Celery, PostgreSQL, Redis, ChromaDB, MinIO, Nginx
- **NEVER** embed LLM in FastAPI. Always HTTP to `LLM_BASE_URL`.

## Tech Stack

| Layer | Tech |
|-------|------|
| Backend | Python 3.11, FastAPI (async), Celery, Redis |
| ORM | SQLAlchemy 2.0 Async + Alembic |
| Vector DB | ChromaDB (legal GraphRAG) |
| Object Storage | MinIO (PDFs) |
| Frontend | Vue 3 Composition API, Pinia, Axios, WebSocket |
| Tool mocks | Gemini Flash API |

## Core Flow — ReAct Appraisal

1. `POST /api/v1/dossiers/{id}/appraise` → create Celery task → `202 Accepted`
2. Celery worker: Reason → Tool Call → Observe loop
3. LLM calls via `llm_client.chat_completions()`
4. Tool execution via `services/tools/` (Gemini Flash mock)
5. **Every tool call** → `ai_audit_logs` (tool_name, inputs, outputs, duration_ms)
6. Progress → Redis Pub/Sub → WebSocket `/ws/appraisal/{dossier_id}`
7. Compute risk HIGH/MEDIUM/LOW from rules
8. Save `appraisal_results` (report_md, resolution_md, checks JSONB)

## Database Schema

### users
`id`, `name`, `email`, `role` (admin, hdtv_leader, dept_head, specialist), `is_active`

### dossiers
`id`, `doc_no`, `title`, `unit`, `risk_level`, `status` (pending, appraising, approved, needs_revision), `pdf_url`

### appraisal_results
`id`, `dossier_id`, `overall_risk`, `report_md`, `resolution_md`, `checks` (JSONB)

### alerts
`id`, `dossier_id`, `severity`, `source`, `description`, `status` (open, resolved)

### ai_audit_logs (CRUCIAL)
`id`, `task_id`, `tool_name`, `execution_time_ms`, `inputs` (JSONB), `outputs` (JSONB), `created_at`

## Risk Rules

| Condition | Risk |
|-----------|------|
| Budget exceeded (ERP) | HIGH |
| Inventory waste detected | HIGH |
| Legal doc missing/expired | MEDIUM |
| All checks pass | LOW |

## Tool Registry

| Tool | Mock via Gemini |
|------|-----------------|
| ErpBudgetCheck | ERP budget vs proposal |
| ErpInventoryCheck | ERP MM/INV stock |
| DOfficeLookup | Document registry |
| PmisProjectCheck | Project management |
| LegalGraphRAG | ChromaDB legal docs |
| EcoOcrExtract | OCR text extraction |

## API Endpoints

- `GET /api/v1/health` → `{"status":"ok"}`
- `GET /api/v1/dossiers` — list
- `GET /api/v1/dossiers/{id}` — detail + latest appraisal
- `POST /api/v1/dossiers/{id}/appraise` — start task (202)
- `GET /api/v1/alerts` — list alerts
- `PATCH /api/v1/alerts/{id}/resolve` — resolve alert
- `GET /api/v1/audit-logs` — admin audit trail

## WebSocket Events

`/ws/appraisal/{dossier_id}`: `started`, `tool_executing`, `tool_result`, `risk_flagged`, `completed`

## Code Conventions

1. Async everywhere (`httpx`, async SQLAlchemy)
2. Router → Service → Repository — no business logic in routers
3. All config via Pydantic `BaseSettings` + `.env`
4. Strict type hints on all functions
5. Path: `project_devops/apps/hdtv-ai-platform/`
