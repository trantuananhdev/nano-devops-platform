# Project State — EVN HDTV AI

**Phase**: 12 — EVN Production Feature Complete (IN PROGRESS ✨)
**Last updated**: 2026-06-12 (session 21 — Phase 11 complete, Phase 12 T-43 done)
**Demo ready**: yes (with real dossier 198/TTr-EVNHANOI data)

## Verified Endpoints

| Endpoint | Status |
|----------|--------|
| `GET /api/v1/health` | implemented |
| `GET /api/v1/dossiers` | implemented |
| `POST /api/v1/dossiers/{id}/appraise` | implemented (T-16: +`?user_id=`; T-17: plan-execute-reflect; T-23: role profiles via body/query `user_id`) |
| `GET /api/v1/audit-logs` | implemented |
| `GET /api/v1/alerts` | implemented |
| `GET /api/v1/tools` | implemented |
| `GET /api/v1/dashboard/summary` | implemented |
| `GET /api/v1/knowledge-graph` | implemented |
| `GET /api/v1/schedules` | implemented |
| `GET /api/v1/skills` | implemented |
| `GET /api/v1/checklist-template` | implemented |
| `WS /ws/appraisal/{id}` | implemented (+ T-17: `plan_created`, `plan_revised`, `step_completed`; T-19: `critic_review`; T-22: `clarification_needed`, `clarification_answered`) |
| `GET /api/v1/search?q=` | T-11 — Meilisearch full-text, graceful degraded |
| `GET /api/v1/workflows/{dossier_id}` | T-12 — BPMN load from DB |
| `PUT /api/v1/workflows/{dossier_id}` | T-12 — BPMN save to DB + audit log |
| `GET /api/v1/workflows` | T-12 — list all saved diagrams |
| `POST /api/v1/dossiers` | T-13 — create dossier (201/409 duplicate) |
| `POST /api/v1/dossiers/{id}/upload` | T-13 — PDF upload to MinIO |
| `GET /api/v1/dossiers/{id}/pdf-url` | T-14 — presigned MinIO URL |
| `GET /api/v1/users` | T-14 — admin user list |
| `GET /api/v1/roles` | T-14 — role definitions |
| `GET /api/v1/system-logs` | T-14 — system activity log |
| `GET /api/v1/users/{id}/preferences` | T-16 — get user preferences |
| `PUT /api/v1/users/{id}/preferences` | T-16 — upsert user preferences |
| `POST /api/v1/dossiers/{id}/feedback` | T-20 — submit appraisal feedback (201) |
| `GET /api/v1/feedback/stats` | T-20 — aggregate feedback counts |
| `GET /api/v1/clarifications/pending` | T-22 — pending HITL clarifications |
| `POST /api/v1/clarifications/{id}/answer` | T-22 — answer + resume appraisal |
| `GET /api/v1/agent/metrics` | T-24 — plan_revision_rate, critic_rejection_rate, feedback_total, memory_retrieval_count |
| `GET /api/v1/api-keys` | T-33 — list API keys (Gemini, MCP, MinIO, Internal) |
| `POST /api/v1/api-keys` | T-33 — create API key (hashed, prefix visible) |
| `DELETE /api/v1/api-keys/{id}` | T-33 — deactivate API key |
| `GET /api/v1/mcp/manifest` | T-36 — MCP server manifest |
| `POST /api/v1/mcp/tools/list` | T-36 — MCP tools list (DB ApiKey auth) |
| `POST /api/v1/mcp/tools/call` | T-36 — MCP tool call (audit log to mcp_call_logs) |
| `POST /api/v1/mcp/tools/call/stream` | T-36 — MCP SSE streaming (audit log) |
| `GET /api/v1/mcp/audit-logs` | T-36 — MCP call audit logs |
| `GET /api/v1/mcp/health` | T-36 — MCP server health check |

## FE Views Wired

| View | Data source |
|------|-------------|
| Dashboard | `/dashboard/summary` |
| DossierList / Workspace | dossiers + WS |
| Alerts / Admin | alerts + audit-logs |
| Chat | dossiers + appraise + WS + audit |
| Tools | `/tools` |
| Graph | `/knowledge-graph` + dossiers |
| Schedule | `/schedules` |
| Skills | `/skills` + dossiers |
| Settings | `/checklist-template` + dossiers |
| Workflow | T-12 BPMN via `/workflows/{id}` |
| GlobalSearch | T-11 Meilisearch Ctrl+K |
| DossierList | T-13 wizard + PDF upload |
| SystemAdmin | T-14 Users/Roles/System Logs + T-24 Agent Intelligence tab + T-33 API Keys Management tab + T-36 MCP Audit Logs tab |
| Workspace | T-14 iframe PDF viewer + T-20 👍/👎 feedback + T-22 clarification modal |

## Agent Level 4 Progress

| Feature | Status |
|---------|--------|
| Vector Memory (Chroma HTTP) | **T-15 DONE** |
| Cross-dossier Memory + User Prefs | **T-16 DONE** |
| Plan-Execute-Reflect Orchestrator | **T-17 DONE** |
| Parallel Tool Executor | **T-18 DONE** |
| Critic Module | **T-19 DONE** |
| Feedback Loop | **T-20 DONE** |
| Tool Chaining & Composition | **T-21 DONE** |
| Human-in-the-Loop (HITL) | **T-22 DONE** |
| Role-Based Agent Profiles | **T-23 DONE** |
| Agent Intelligence Dashboard | **T-24 DONE** — Phase 8 complete |

## T-17/T-18 Architecture

```
POST /appraise → Celery → run_appraisal()
    │
    ├─ retrieve_feedback_lessons() (T-20) ← Chroma feedback_lessons → planner prompt
    ├─ planner.create_plan()     ← LLM HTTP (Gemma Ubuntu); parallel_group hint
    ├─ persist agent_plans row
    ├─ WS: plan_created
    │
    ├─ executor.execute_plan_steps()  ← batches by parallel_group (T-18)
    │       ├─ batch_executor.execute_parallel() via asyncio.gather
    │       ├─ ai_audit_logs per tool (2 rows for financial batch)
    │       ├─ chain_executor after each tool (T-21: EcoOcrExtract → LegalGraphRAG)
    │       └─ WS: step_completed, tool_executing, tool_result (+ wall_time_ms)
    │
    ├─ reflector.reflect_on_results() ← LLM or rule fallback
    │       └─ if revise (max 2): WS plan_revised → re-execute revised steps
    │
    ├─ critic.review_draft() (T-19) ← LLM or rule fallback
    │       ├─ WS: critic_review
    │       └─ if rejected (max 2): re-execute failed tools → regenerate report
    │
    ├─ HITL pause (T-22) ← tool conflict or low confidence
    │       ├─ agent_clarifications row + resume_state in DB
    │       ├─ WS: clarification_needed
    │       └─ POST answer → resume_appraisal_task → completed
    │
    └─ legacy ReAct fallback if orchestration raises
```

**Orchestrator files:** `planner.py`, `executor.py`, `reflector.py`, `critic.py`, `helpers.py`, `types.py`, `batch_executor.py`, `chain_executor.py`, `clarification_service.py`, `prompt_builder.py`, `prompts/`

## T-23 Role Profiles

| Role | user_id (seed) | Resolution style |
|------|----------------|------------------|
| `hdtv_leader` | 1 | Concise risk-first (`tóm tắt HĐTV`) |
| `dept_head` | 2 | Checklist + supplement recommendations |
| `admin` | 3 | Full audit trail, no summarization |
| `specialist` | 4 | Full technical report |

`POST /appraise?user_id=1` vs `user_id=4` → different `resolution_md` length/focus via `prompt_builder.build_resolution_md()`.
Planner + legacy ReAct + LLM summary all use role-specific prompts.

## T-21 Tool Chain (seeded)

| Source | Target | Mapping |
|--------|--------|---------|
| `EcoOcrExtract` | `LegalGraphRAG` | `extracted_text` → `query` |

## T-22 HITL Triggers

| Trigger | Condition | Options |
|---------|-----------|---------|
| `tool_conflict` | ErpBudgetCheck fail + ErpInventoryCheck fail | prioritize_budget / prioritize_inventory / both_escalate |
| `low_confidence` | reflector `escalate` or mixed pass/fail | accept_and_continue / request_more_checks |

## T-24 Agent Metrics

| Metric | Source |
|--------|--------|
| `plan_revision_rate` | `agent_plans` where `revision > 0` / total plans |
| `critic_rejection_rate` | `appraisal_results.critic_verdict.approved=false` / appraisals with verdict |
| `feedback_total` | `agent_feedbacks` count (approve/reject/adjust) |
| `memory_retrieval_count` | `agent_memories` rows (vector memory footprint) |

Admin tab **Agent Intelligence** at `/admin` → 4 KPI cards + drill-down counts.

## Code Quality Pass (session 15)

| Fix | File | Issue |
|-----|------|-------|
| `tasks.py` formatting | `app/workers/tasks.py` | Double-newline artifact from copy-paste — cleaned up |
| `eval()` sandbox hardened | `react_agent.py` | `_eval_rule_expression()` with whitelisted builtins (`len`, `any`, `all`, `sum`, etc.) + pre-computed `failed`/`passed`/`failed_tools` context |
| Import inside function | `memory/retriever.py` | `import httpx` + internal imports moved to module top |
| SQLAlchemy bool comparison | `tools/base.py`, `meta_service.py` | `== True` → `.is_(True)` |
| `build_check` sync | `orchestrator/helpers.py` + callers | Removed spurious `async` — sync fn awaited unnecessarily |
| LLM client retries | `services/llm_client.py` | Added `max_retries=2` loop over transient errors, fallback constant extracted |

## Phase 9 Progress (session 17)

| Task | Status | Key files |
|------|--------|-----------|
| T-25: LLM Circuit Breaker | **DONE** | `app/core/circuit_breaker.py`, `llm_router.py`, `tasks.py` |
| T-26: Sandbox Audit + Docker | **DONE** | `tools/docker_sandbox.py`, `tools/sandbox_executor.py` |
| T-27: RAG Ingestion Pipeline | **DONE** | `workers/rag_pipeline.py`, `workers/celery_app.py`, `core/context_manager.py` |
| T-28: Observability LLMOps | **DONE** | `platform/alerts/hdtv-alerts.yml`, `grafana/hdtv-agent.json`, `app/core/tracing.py` |
| T-29: MCP SSE + Validation | **DONE** | `routers/mcp.py` (SSE+validation), `traefik/dynamic.yml`, `docker-compose` Traefik labels |
| T-30: Execution Harness | **DONE** | `tools/base.py` input validation + handler wiring, per-tool timeout, retry, `010_audit_log_harness.py` |

### T-30 Implementation Summary
- `base.py`: `ToolErrorType` enum (TRANSIENT/BAD_INPUT/UNAVAILABLE/UNKNOWN); `_TOOL_INPUT_REQUIRED_FIELDS` dict cho 7 tools; `_validate_tool_input()` checks required fields + types; `execute_tool()` hai tầng validation (schema → handler domain-level) → `asyncio.wait_for(tool_execution_timeout_s)` → error taxonomy trên mọi path
- **Handler wiring** (self-critique fix): `get_handler()` được gọi sau `_validate_tool_input()` trong `execute_tool()` → domain-level validation (doc_no format, dossier_id > 0) thực sự được invoke, không chỉ exist
- `batch_executor.py`: `_run_one_with_retry()` với `max_retries`/`retry_backoff_s` params; retry chỉ TRANSIENT/UNKNOWN; `TOOL_RETRIES` metric; `retried` flag trong result
- `executor.py`: `AiAuditLog` ghi `plan_step_id=plan_step.get("id")` và `error_type=str(output.get("error_type"))` → audit correlation agent_plans → trace span
- `entities.py`: `AiAuditLog.plan_step_id` (String 64, nullable, index) + `AiAuditLog.error_type` (String 32, nullable)
- `010_audit_log_harness.py`: ADD COLUMN plan_step_id + error_type + index `ix_ai_audit_logs_plan_step_id`
- `config.py`: `tool_execution_timeout_s=30`, `tool_max_retries=1`, `tool_retry_backoff_s=2.0`
- `metrics.py`: `TOOL_RETRIES` (tool_name, error_type), `TOOL_TIMEOUTS` (tool_name), `TOOL_INPUT_VALIDATION_ERRORS` (tool_name)
- `app/tools/handlers/__init__.py`: package doc — convention cho future handlers
- `app/tools/handlers/erp_handler.py`: `ErpBudgetHandler` + `ErpInventoryHandler` với `validate_input()` (domain VND, doc_no format) + `execute()` (delegate Gemini mock); `get_handler()` registry function
- `docker-compose.hdtv.yml`: `beat` service (64m) đã có từ T-27 — confirmed

### T-28 Implementation Summary
- `hdtv-alerts.yml`: 14 Prometheus alert rules — HdtvApiDown, HdtvLlmCircuitOpen, HdtvAgentInfiniteLoop, HdtvToolHighFailureRate, HdtvAppraisalTimeout, HdtvSandboxHighBlockRate, HdtvContextTruncationSpike + 7 bonus rules
- `hdtv-agent.json`: 5-row Grafana dashboard (LLM Health, Agent Loop, Tool Execution, RAG/Memory, Infrastructure)
- `tracing.py`: lazy OTel import, OTLP gRPC → `platform-jaeger:4317`, `configure_tracer()` + `instrument_fastapi()`
- `main.py`: tracing opt-in via `settings.tracing_enabled` (default False)
- `requirements.txt`: pinned `opentelemetry-sdk==1.24.0`, otlp-grpc, instrumentation-fastapi
- `docker-compose.hdtv.yml`: Prometheus Docker SD labels on `api` + `platform-network` bridge
- `prometheus.yml`: static job `hdtv-ai` + auto-discovery via Docker SD

### T-29 Implementation Summary
- `mcp.py` (rewritten):
  - `_TOOL_OUTPUT_SCHEMAS`: required output fields cho 6 tools (ErpBudgetCheck, ErpInventoryCheck, DOfficeLookup, PmisProjectCheck, LegalGraphRAG, EcoOcrExtract)
  - `_validate_tool_output()`: annotates missing fields with hints (non-blocking — agent gets guidance not exception)
  - `POST /mcp/tools/call/stream`: SSE via `asyncio.Queue` + background task; events: `progress` (2s keepalive), `result` (validated output), `error`
  - `mcp_manifest()`: `capabilities.streaming.supported = True`
  - `_validate_tool_output` called in both `/call` and `/call/stream`
- `traefik/dynamic.yml`: HTTP routers `hdtv-http` (redirect), `hdtv-https`, `hdtv-mcp` (priority 10, mcp-ratelimit@file); `hdtv-api` service upstream + healthCheck
- `docker-compose.hdtv.yml`: Traefik labels với router rules, TLS, middleware ref, service port 8000
- `Vagrantfile`: `hdtv.nano.platform` đã có trong PLATFORM_DOMAINS

### T-25 Implementation Summary
- `CircuitBreaker` class: CLOSED/OPEN/HALF_OPEN states, asyncio.Lock, sliding window failure tracking
- `_get_cb_gemini()` / `_get_cb_local()` lazy singletons in `llm_router.py`
- Gemini key rotation upgraded: `_key_cooldown` dict skips 429/403 keys for 60s
- `tasks.py`: `asyncio.wait_for(appraisal_max_duration_s)` → timeout → `needs_revision` + WS `timeout` event
- Metrics: `hdtv_llm_circuit_trips_total` (backend, role), `hdtv_appraisal_timeouts_total`

### T-26 Implementation Summary
- `docker_sandbox.py`: `DockerSandboxExecutor` with `--network none --memory --cpus --read-only`, fallback to process sandbox
- `sandbox_executor.py`: `_emit_sandbox_audit()` writes `AiAuditLog` (tool_name="SandboxShell") after every execution
- `SANDBOX_EXECUTIONS` counter with type=shell|python, status=success|blocked|timeout|error
- Config: `sandbox_use_docker=False` (safe default), `sandbox_docker_image`, `sandbox_docker_timeout_s=15`
- docker-compose: Docker socket mount instructions (commented), `hdtv_rag_docs` volume on worker

### T-27 Implementation Summary
- `rag_pipeline.py`: 2 Celery tasks
  - `ingest_legal_documents`: sliding window chunk (512 tok, 64 overlap), upsert to Chroma `legal_docs`, `RagIngest` audit log
  - `cleanup_stale_embeddings`: delete docs with `ingested_at` > 30 days
- `celery_app.py`: beat_schedule — ingest every 6h, cleanup daily 02:00 (Asia/Ho_Chi_Minh)
- `context_manager.py`: `fit_messages()` now emits `CONTEXT_TRUNCATIONS` (lazy import, try/except safe); de-duplicated from `llm_router.py` to prevent double-count
- `vector_store.py`: `upsert_legal_doc(doc_id, text, metadata)` + `query_legal_docs(query, top_k)` for `legal_docs` collection
- `legal_rag.py`: queries both seeded collection (T-08) and RAG pipeline collection; `_deduplicate_results()` by title; caps at 5 results
- docker-compose: `beat` service (64m RAM), `hdtv_rag_docs` named volume shared between worker + beat

## Phase 10 Progress (session 20)

| Task | Status | Key files |
|------|--------|-----------|
| T-31: LLM Node Professionalization (Caddy + Metrics + Logs) | **DONE** | `ansible-ubuntu/roles/llm_node/` (Caddy, node-exporter, promtail), `cli.sh` (_generate_llm_node_targets) |
| T-32: Observability Completeness & Alertmanager | **DONE** | `platform/config/prometheus/alerts/hdtv-alerts.yml`, `alertmanager.yml` |
| T-33: API Keys Management Dashboard | **DONE** | `app/models/entities.py` (ApiKey), `app/routers/api_keys.py`, `admin.js`, `SystemAdminView.vue` (API Keys tab), `011_add_api_keys.py` |
| T-34: HDTV Workflow Grafana Dashboard | **DONE** | `platform/monitoring/grafana/dashboards/hdtv-workflow.json` |
| T-35: Backup Strategy | **DONE** | `scripts/backup.sh`, `cli.sh` (hdtv-backup) |
| T-36: MCP Token Management & Audit | **DONE** | `app/models/entities.py` (McpCallLog), `app/routers/mcp.py`, `SystemAdminView.vue` (MCP Audit tab), `012_mcp_call_logs.py` |
| T-37: LLM Node Teardown & Reset | **DONE** | `ansible-ubuntu/teardown-llm.yml`, `cli.sh` (ansible-teardown-llm, ansible-teardown-full) |

### T-31 Implementation Summary
- Ansible role `llm_node`: adds Caddy reverse proxy (8080 → 127.0.0.1:8081, 8443 HTTPS self-signed), Prometheus node-exporter (9100), Promtail shipping logs to Alpine Loki
- `cli.sh`: adds `_generate_llm_node_targets()` that creates `llm-node-targets.yml` and `llm-node-probe-targets.yml` from .env ACER_HOST on `up`
- Observability: Prometheus scrapes LLM node, Grafana dashboards for infrastructure

### T-33 Implementation Summary
- `ApiKey` entity: id, name, key_type, key_prefix, hashed_key, is_active, created_by, created_at, last_used_at
- `api_key_service.py`: CRUD operations, bcrypt hashing, verification, DB-first lookup with .env fallback
- `llm_router.py`: `_next_gemini_key()` pulls active Gemini keys from DB first
- FE SystemAdminView: API Keys tab with add/delete, copy, filter by type; creates key modal with show/hide raw key
- Migration: `011_add_api_keys.py`

### T-36 Implementation Summary
- `McpCallLog` entity: id, tool_name, api_key_prefix, is_streaming, execution_ms, is_error, output_incomplete, created_at
- `mcp.py`: `_require_mcp_key()` uses DB ApiKey auth (type: mcp), `_log_mcp_call()` writes every call (sync/stream) to mcp_call_logs
- FE SystemAdminView: MCP Audit Logs tab with filter/search, recent calls table
- Migration: `012_mcp_call_logs.py`

### T-37 Implementation Summary
- `teardown-llm.yml`: Ansible playbook that stops LLM docker-compose, removes containers/volumes, deletes /opt/llm-node; optional full wipe with `wipe_docker=true` (uninstalls Docker Engine)
- `cli.sh`: adds commands `ansible-teardown-llm` and `ansible-teardown-full`

## Docker Compose Quality Pass (session 19)

### `platform/composition/docker-compose.hdtv.yml` — canonical VM file

| Fix | Detail |
|-----|--------|
| Bỏ `version: "3.8"` | Deprecated trong Docker Compose v2, gây warning |
| Pin `minio` image | `minio:latest` → `minio:RELEASE.2024-11-07T00-52-20Z` |
| Healthcheck `hdtv-chroma` | Thêm `curl /api/v1/heartbeat` — trước đây không có → `depends_on` không có condition |
| Healthcheck `hdtv-minio` | Thêm `curl /minio/health/live` |
| `x-hdtv-services` bổ sung | Thêm `MINIO_ROOT_USER` + `MINIO_ROOT_PASSWORD` vào anchor → worker/beat đều có qua `<<:` merge |
| `hdtv-api depends_on` | Thêm `hdtv-chroma` + `hdtv-minio` với `condition: service_healthy` |
| `hdtv-worker depends_on` | `service_started` → `service_healthy` cho `hdtv-api` |
| `hdtv-frontend depends_on` | `- hdtv-api` (list) → `hdtv-api: condition: service_healthy` |
| Comment build context | Clarify path resolution relative to file directory |

### `apps/hdtv-ai-platform/docker-compose.hdtv.yml` — standalone dev file

| Fix | Detail |
|-----|--------|
| Pin `minio` image | `latest` → `RELEASE.2024-11-07T00-52-20Z` |
| `worker` env | Thêm `MINIO_ENDPOINT`, `MINIO_ROOT_USER`, `MINIO_ROOT_PASSWORD` |
| `worker depends_on api` | `service_started` → `service_healthy` |

### Kết luận architecture

- `platform/composition/docker-compose.hdtv.yml` = **production path** — `cli.sh hdtv-up` dùng file này
- `apps/hdtv-ai-platform/docker-compose.hdtv.yml` = **standalone dev** — chạy độc lập không cần core stack (có postgres/redis riêng)
- Không nên xoá `apps/` file — nó là để dev local / CI build test riêng lẻ



```bash
./cli.sh ansible-teardown-llm # Optional: reset Ubuntu LLM node to clean state
./cli.sh ansible-deploy-llm   # Ubuntu LLM (Caddy + node-exporter + promtail)
./cli.sh obs-down             # Optional: stop observability stack to save RAM
./cli.sh hdtv-up              # Alpine app stack (includes beat service for RAG pipeline)
./cli.sh hdtv-migrate         # Run all migrations (001–012: NEW: 011_api_keys, 012_mcp_call_logs)
./cli.sh hdtv-seed            # Seed DB + Chroma + Meilisearch + agent_memories
./cli.sh hdtv-backup          # Optional: run backup (Postgres + MinIO + Chroma)
```

## Demo URL

- FE: `http://<VM_IP>:3080` or `https://hdtv.nano.platform`
- API docs: `http://<VM_IP>:8000/docs`

## RAM Budget Update

| Service | Limit |
|---------|-------|
| postgres | 384m |
| redis | 128m |
| api | 384m |
| worker | 512m |
| beat | 64m (T-27 — Celery beat scheduler) |
| chroma | 400m |
| minio | 256m |
| meilisearch | 256m |
| nginx | 64m |
| **Total** | **~2.45GB** |

---

## Phase 11 — Real Data & UX Optimization (Session 21)

### What's New
- **T-38**: Created data folder structure and copied real EVN PDF dossier files
  - Dossier: 198/TTr-EVNHANOI — Tiêu chuẩn kỹ thuật UAV
  - Files organized in `data/seed/dossier_198_uav/`
  - 10+ real PDF/Excel files from EVN Hanoi

- **T-39**: Enhanced seed.py to upload real PDFs to MinIO
  - Uploads main dossier PDF and all reference documents
  - Updates dossier record with PDF URL

- **T-40**: Implemented PDF text extraction & RAG ingestion
  - Added `PyMuPDF` dependency for fast PDF parsing
  - Created `app/services/rag/pdf_extractor.py`
  - `extract_text_from_pdf()` function for PDF → text
  - `chunk_text()` for vector embedding-friendly chunks
  - Seed script automatically ingests legal docs into Chroma

- **T-41**: UX/UI Optimization
  - DashboardView: Added "Tờ trình mới nhất" widget with grid cards
  - DashboardView: Improved risk badges consistency
  - SplitViewWorkspace: Added proper PDF loading state with spinner
  - SplitViewWorkspace: Optimized PDF viewer layout

### New Files
- `docs-ai-system/99-appendix/HDTV_PHASE11_TASKS.md`: Task list for Phase 11
- `project_devops/apps/hdtv-ai-platform/app/services/rag/__init__.py`: RAG package
- `project_devops/apps/hdtv-ai-platform/app/services/rag/pdf_extractor.py`: PDF extractor
- `project_devops/apps/hdtv-ai-platform/data/seed/dossier_198_uav/`: Real dossier data folder

### Updated Files
- `requirements.txt`: Added `PyMuPDF==1.24.13`
- `seed.py`: Added dossier 198, `seed_dossier_198_pdfs()`, `seed_real_legal_docs()`
- `PROJECT_STATE.md`: Updated to Phase 11
- `project_devops/apps/hdtv-ai-prototype/src/views/DashboardView.vue`: Added "Tờ trình mới nhất" widget
- `project_devops/apps/hdtv-ai-prototype/src/views/SplitViewWorkspace.vue`: Added PDF loading state

### Demo Data Highlights
Dossier **198/TTr-EVNHANOI** includes:
- Tờ trình chính (01_to_trinh_198_TTr_EVNHANOI.pdf)
- Tờ trình 07/KT đã duyệt
- Báo cáo thẩm tra
- Phiếu trình với ý kiến HĐTV
- Phụ lục kỹ thuật (Excel)
- Ý kiến góp ý từ nhà cung cấp Apex & MAJ
- Quyết định 8594/QĐ-EVNHANOI (căn cứ pháp lý)

---

## Phase 12 — EVN Production Feature Complete (In Progress)

### What's New
- **T-43**: User Roles & Permissions (BE)
  - Updated UserOut schema to match real User entity
  - Updated meta_service's list_users and list_roles to use real DB data
  - Added role-based permission utilities in `app/core/permissions.py`
  - Updated `meta.py`'s `/users` and `/roles` endpoints to use DB
- **T-44**: User Roles & Permissions (FE)
  - Updated SystemAdminView.vue: removed dept column, added ROLE_LABELS mapping, updated status display using is_active
  - Created auth.js Pinia store for auth state and role-based checks
- **T-45**: Formal Status Transitions & Workflow (BE)
  - Updated DossierStatus enum with full workflow (draft → submitted_to_dept → dept_approved/dept_rejected → submitted_to_board → board_reviewed → approved/rejected)
  - Added StatusHistory entity to track full audit history of status changes
  - Created workflow_service.py to manage valid transitions and enforce permissions
  - Added status transition endpoint POST /dossiers/{id}/transition-status
  - Added status history endpoint GET /dossiers/{id}/status-history
  - Added migration 013_add_status_history.py
  - Updated seed.py to use new status values

### New Files
- `project_devops/apps/hdtv-ai-platform/app/core/permissions.py`: NEW role-based permission checks
- `project_devops/apps/hdtv-ai-platform/app/services/workflow_service.py`: NEW workflow and status transition service
- `project_devops/apps/hdtv-ai-platform/alembic/versions/013_add_status_history.py`: NEW migration
- `project_devops/apps/hdtv-ai-prototype/src/stores/auth.js`: NEW — auth store with current user state

### Updated Files
- `project_devops/apps/hdtv-ai-platform/app/models/entities.py
- `project_devops/apps/hdtv-ai-platform/app/schemas/meta.py
- `project_devops/apps/hdtv-ai-platform/app/schemas/dossier.py
- `project_devops/apps/hdtv-ai-platform/app/services/meta_service.py
- `project_devops/apps/hdtv-ai-platform/app/routers/meta.py
- `project_devops/apps/hdtv-ai-platform/app/routers/dossiers.py
- `project_devops/apps/hdtv-ai-platform/scripts/seed.py
- `project_devops/apps/hdtv-ai-prototype/src/views/SystemAdminView.vue

---

## Phase 12 — EVN Production Feature Complete (Planned)

### Mục tiêu
Hoàn thiện đầy đủ các tính năng cho quy trình nghiệp vụ thực tế của EVN:
- User roles & permissions (Chuyên viên, Trưởng Ban, Thành viên HĐTV, Lãnh đạo HĐTV, Admin)
- Formal status transitions workflow with audit trail
- Document version control
- Reference document management
- Notification system

### Tasks (T-43 to T-54)
| Task | Priority | Description | Status |
|------|----------|-------------|--------|
| T-43 | P1 | User Roles & Permissions (BE) | ✅ DONE |
| T-44 | P1 | User Roles & Permissions (FE) | ✅ DONE |
| T-45 | P1 | Formal Status Transitions & Workflow (BE) | ✅ DONE |
| T-46 | P1 | Formal Status Transitions & Workflow (FE) | ✅ DONE |
| T-47 | P2 | Document Version Control (BE) | ✅ DONE |
| T-48 | P2 | Document Version Control (FE) | ✅ DONE |
| T-49 | P1 | Audit Trail (BE) | ✅ DONE |
| T-50 | P2 | Audit Trail (FE) | ✅ DONE |
| T-51 | P1 | Reference Document Management (BE) | ✅ DONE |
| T-52 | P1 | Reference Document Management (FE) | ✅ DONE |
| T-53 | P2 | Notification System (BE) | ⏳ PENDING |
| T-54 | P2 | Notification System (FE) | ⏳ PENDING |
