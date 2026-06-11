# HDTV Sprint Tasks

## Status Legend: PENDING | IN_PROGRESS | DONE | BLOCKED

---

### T-01: Infra skeleton
- **deps:** none
- **files:** `hdtv-ai-platform/docker-compose.hdtv.yml`, `app/main.py`, `app/core/config.py`
- **acceptance:** `GET /api/v1/health` returns 200
- **verify_cmd:** `curl -sf http://localhost:8000/api/v1/health`
- **status:** DONE

### T-02: LLM node Ansible
- **deps:** T-01
- **files:** `ansible-ubuntu/roles/llm_node/`, `deploy-llm.yml`
- **acceptance:** llama-server running on Ubuntu :8080
- **verify_cmd:** `curl -sf http://$ACER_HOST:8080/v1/models`
- **status:** DONE

### T-03: Database models + migrations
- **deps:** T-01
- **files:** `app/models/`, `alembic/`
- **acceptance:** All 5 tables exist after migrate
- **verify_cmd:** `./cli.sh hdtv-migrate`
- **status:** DONE

### T-04: Celery ReAct + audit logs
- **deps:** T-03
- **files:** `app/workers/`, `app/services/orchestrator/`
- **acceptance:** POST appraise creates audit log rows
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

### T-05: WebSocket streaming
- **deps:** T-04
- **files:** `app/routers/ws.py`, `app/services/pubsub.py`
- **acceptance:** WS emits started/completed events
- **verify_cmd:** test.sh ws section
- **status:** DONE

### T-06: FE wire core views
- **deps:** T-05
- **files:** `hdtv-ai-prototype/src/stores/`, `src/services/`
- **acceptance:** DossierList, Workspace, Admin, Alerts use API
- **verify_cmd:** `npm run build` in hdtv-ai-prototype
- **status:** DONE

### T-07: Tool mocks Gemini
- **deps:** T-04
- **files:** `app/services/tools/`
- **acceptance:** 5+ tools registered and logged
- **verify_cmd:** test.sh tools section
- **status:** DONE

### T-08: Chroma seed + LegalGraphRAG
- **deps:** T-07
- **files:** `app/services/rag/`, `scripts/seed.py`
- **acceptance:** Legal tool returns seeded docs
- **verify_cmd:** `./cli.sh hdtv-seed`
- **status:** DONE

### T-09: CI + demo runbook
- **deps:** T-01
- **files:** `.github/workflows/ci.yml`, `HDTV_DEMO_RUNBOOK.md`
- **acceptance:** CI builds hdtv images
- **verify_cmd:** review workflow yaml
- **status:** DONE

### T-10: Wire remaining FE views
- **deps:** T-06
- **files:** `hdtv-ai-prototype/src/views/` (Dashboard, Chat, Workflow, Graph, Schedule, Skills, Tools, Settings), `app/routers/meta.py`, `app/services/meta_service.py`
- **acceptance:** 8 views load data from API; meta endpoints respond
- **verify_cmd:** `npm run build` in hdtv-ai-prototype && `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

#### T-10 View backlog

| View | Store | API | Status |
|------|-------|-----|--------|
| DashboardView | `dashboard.js` | `GET /dashboard/summary` | DONE |
| AdvancedChatView | `chat.js` | dossiers + appraise + WS + audit-logs | DONE |
| WorkflowManager | `workflow.js` + `dossier.js` | `GET/PUT /workflows/{id}` | DONE |
| KnowledgeGraphView | `graph.js` + `dossier.js` | `GET /knowledge-graph` | DONE |
| ScheduleManagerView | `schedule.js` | `GET /schedules` | DONE |
| SkillBuilderView | `skills.js` + `dossier.js` | `GET /skills` | DONE |
| ToolRegistryView | `tools.js` | `GET /tools` | DONE |
| DossierSettingsView | `settings.js` + `dossier.js` | `GET /checklist-template` | DONE |

### T-11: Meilisearch full-text search
- **deps:** T-01, T-03
- **files:**
  - `docker-compose.hdtv.yml` — meilisearch service (256MB, v1.8)
  - `app/core/config.py` — meili_url, meili_api_key, meili_index_dossiers
  - `app/services/search_service.py` — httpx async, ensure_index, index_dossier, search_dossiers
  - `app/routers/search.py` — GET /api/v1/search?q=&risk=&status=
  - `scripts/seed.py` — seed_meilisearch() after DB seed
  - `app/main.py` — warmup search index on startup (fire-and-forget)
  - `hdtv-ai-prototype/src/stores/search.js` — Pinia store
  - `hdtv-ai-prototype/src/components/GlobalSearch.vue` — Ctrl+K modal with highlight, degraded mode
  - `hdtv-ai-prototype/src/App.vue` — wire GlobalSearch into sidebar
  - `hdtv-ai-prototype/src/services/api.js` — searchDossiers export
- **acceptance:** GET /search?q=tờ+trình returns {"hits":[...]} (degraded=true if Meili unreachable, not 500)
- **verify_cmd:** `curl -sf 'http://localhost:8000/api/v1/search?q=tờ+trình' | grep -q '"hits"'`
- **status:** DONE

### T-12: BPMN workflow persistence
- **deps:** T-06
- **files:**
  - `app/models/entities.py` — WorkflowDiagram model (unique per dossier_id)
  - `alembic/versions/002_add_workflow_diagrams.py` — migration
  - `app/services/workflow_service.py` — get/save/list, audit log on every Save
  - `app/routers/workflow.py` — GET/PUT /api/v1/workflows/{dossier_id}
  - `app/routers/__init__.py` — register workflow router
  - `hdtv-ai-prototype/src/stores/workflow.js` — Pinia store
  - `hdtv-ai-prototype/src/views/WorkflowManager.vue` — Save/Load from API, "Đã lưu" timestamp, Export XML
  - `hdtv-ai-prototype/src/services/api.js` — getWorkflow, saveWorkflow, listWorkflows exports
- **acceptance:** PUT /workflows/1 → 200; GET /workflows/1 → same bpmn_xml; audit_logs has WorkflowSave
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

### T-13: Dossier Create + PDF Upload to MinIO
- **deps:** T-01, T-03, T-11
- **files:**
  - `requirements.txt` — add `minio>=7.2.0`
  - `app/services/minio_service.py` — **NEW** async MinIO client (sync SDK + asyncio.to_thread)
  - `app/schemas/dossier.py` — `DossierCreate`, `UploadResult` schemas
  - `app/services/dossier_service.py` — `create_dossier()`, `update_pdf_url()` functions
  - `app/routers/dossiers.py` — `POST /dossiers` (201), `POST /dossiers/{id}/upload` (multipart)
  - `hdtv-ai-prototype/src/stores/dossier.js` — `createNewDossier()`, `uploadPdf()` store actions
  - `hdtv-ai-prototype/src/services/api.js` — `createDossier`, `uploadDossierPdf` exports
  - `hdtv-ai-prototype/src/views/DossierListView.vue` — 3-step wizard modal (metadata → PDF → done)
  - `test.sh` — T-13 verify cases
- **acceptance:** POST /dossiers → 201 with doc_no; duplicate → 409; upload route → not 404; DossierCreate in audit-logs
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

### T-14: Admin panel wire + PDF viewer + Meilisearch sync
- **deps:** T-06, T-11, T-13
- **files:**
  - `app/routers/meta.py` — GET /users, /roles, /system-logs
  - `app/services/meta_service.py` — static admin seeds
  - `app/routers/dossiers.py` — GET /dossiers/{id}/pdf-url (presigned MinIO)
  - `app/schemas/dossier.py` — PdfUrlOut
  - `app/services/search_service.py` — dossier_to_doc() helper
  - `app/services/orchestrator/react_agent.py` — re-index Meilisearch after appraisal
  - `hdtv-ai-prototype/src/stores/admin.js` — fetchUsers/Roles/SystemLogs
  - `hdtv-ai-prototype/src/views/SystemAdminView.vue` — wire tabs to API
  - `hdtv-ai-prototype/src/views/SplitViewWorkspace.vue` — iframe PDF when uploaded
  - `hdtv-ai-prototype/src/services/api.js` — getDossierPdfUrl export
  - `test.sh` — T-14 verify cases
- **acceptance:** Admin tabs load from API; GET /pdf-url returns presigned URL or 404; search index updates after appraisal
- **verify_cmd:** `npm run build` in hdtv-ai-prototype && `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

---

## Phase 8 — Agent Level 4 Upgrade

> **Mục tiêu:** Nâng agent từ Level 2-3 lên Level 4 — vector memory, plan-execute-reflect, critic, feedback loop, parallel tools, role-based personalization.
> **Thứ tự:** T-15 → T-24 tuần tự; mỗi task mở rộng `test.sh` với section riêng.

### T-15: Vector Memory Service (Chroma)
- **deps:** T-08, T-14
- **files:**
  - `requirements.txt` — add `chromadb>=0.5.0` client (HTTP to existing Chroma container)
  - `app/core/config.py` — `chroma_collection_memories`, `memory_top_k`, `memory_embed_model` (optional)
  - `app/services/memory/__init__.py` — **NEW** package
  - `app/services/memory/vector_store.py` — **NEW** upsert/query Chroma collection `agent_memories`
  - `app/services/memory/retriever.py` — **NEW** `retrieve_relevant_memories(dossier_id, query, top_k)` with degraded fallback (append all PG rows)
  - `alembic/versions/004_add_memory_embeddings.py` — add `embedding_id` (String 128, nullable) to `agent_memories`
  - `app/models/entities.py` — `embedding_id` column on `AgentMemory`
  - `app/services/orchestrator/react_agent.py` — after each step: upsert to Chroma; before LLM call: retrieve top_k instead of full observations dump
  - `scripts/seed.py` — optional `seed_agent_memories()` for demo retrieval
  - `test.sh` — T-15 verify cases
- **acceptance:** Appraisal writes `embedding_id` on agent_memories rows; retriever returns ≤`memory_top_k` chunks; degraded mode works when Chroma unreachable (no 500)
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

### T-16: Cross-dossier Memory + User Preferences
- **deps:** T-15
- **files:**
  - `app/models/entities.py` — **NEW** `UserPreference` model (`user_id`, `key`, `value` JSONB)
  - `alembic/versions/005_user_preferences.py` — migration
  - `app/services/memory/retriever.py` — cross-dossier query by `unit`, `risk_level` metadata filter; inject user prefs into context
  - `app/services/memory/preference_service.py` — **NEW** get/set preferences per user
  - `app/routers/meta.py` — `GET/PUT /api/v1/users/{id}/preferences`
  - `app/schemas/meta.py` — `UserPreferenceOut`, `UserPreferenceUpdate`
  - `scripts/seed.py` — seed prefs for demo users (hdtv_leader → `report_style: concise`, specialist → `report_style: detailed`)
  - `test.sh` — T-16 verify cases
- **acceptance:** GET `/users/1/preferences` returns seeded prefs; retriever can query memories across dossiers with same `unit`; system prompt includes preference snippet when `user_id` provided
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

### T-17: Plan-Execute-Reflect Orchestrator
- **deps:** T-15, T-16
- **files:**
  - `app/services/orchestrator/planner.py` — **NEW** LLM plan phase → JSON `{goal, steps:[{id, tool, parallel_group, depends_on}], max_revisions}`
  - `app/services/orchestrator/executor.py` — **NEW** run plan steps sequentially (parallel_group deferred to T-18)
  - `app/services/orchestrator/reflector.py` — **NEW** verdict: `sufficient|revise|escalate` + optional `revised_steps`
  - `app/services/orchestrator/react_agent.py` — refactor to planner→executor→reflector loop (max 2 revisions); keep audit + AgentMemory writes
  - `app/models/entities.py` — **NEW** `AgentPlan` model (`dossier_id`, `plan_json`, `revision`, `status`)
  - `alembic/versions/006_agent_plans.py` — migration
  - `app/services/pubsub.py` — no change required; emit from orchestrator
  - `app/services/orchestrator/react_agent.py` — WS events: `plan_created`, `plan_revised`, `step_completed`
  - `test.sh` — T-17 verify cases
- **acceptance:** POST appraise creates `agent_plans` row with `plan_json`; WS emits `plan_created` before first tool; reflect can trigger one revision; fallback to legacy sequential if plan JSON invalid
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

### T-18: Parallel Tool Executor
- **deps:** T-17
- **files:**
  - `app/services/tools/batch_executor.py` — **NEW** `execute_parallel(tools: list[dict])` via `asyncio.gather`; each call still logs separate `AiAuditLog`
  - `app/services/orchestrator/executor.py` — group steps by `parallel_group`; dispatch parallel batch
  - `app/services/orchestrator/planner.py` — prompt allows same `parallel_group` for independent tools (e.g. ErpBudgetCheck + ErpInventoryCheck)
  - `app/services/orchestrator/react_agent.py` — remove "don't call multiple tools in parallel" from system prompt
  - `test.sh` — T-18 verify cases (grep batch_executor usage; parallel_group in plan seed/mock)
- **acceptance:** Plan with `parallel_group: "financial"` runs 2 ERP tools concurrently; 2 separate audit log rows; total wall time logged
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

### T-19: Critic Module (Self-Reflection)
- **deps:** T-17
- **files:**
  - `app/services/orchestrator/critic.py` — **NEW** `review_draft(report_md, checks, risk_level)` → `{approved, issues, suggested_fixes}`
  - `app/services/orchestrator/react_agent.py` — call critic before final `AppraisalResult`; if `approved=false` and revision < 2 → re-execute missing tools or regenerate report
  - `app/models/entities.py` — optional `critic_verdict` JSONB on `AppraisalResult` (migration `007_critic_verdict.py`)
  - `app/services/pubsub.py` — WS event `critic_review` with verdict
  - `test.sh` — T-19 verify cases
- **acceptance:** Critic module exists and is invoked; `AppraisalResult` stores critic verdict; mock high-risk checks + low-risk draft → critic rejects (`approved: false`)
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

### T-20: Feedback API + Learning Loop
- **deps:** T-15, T-17
- **files:**
  - `app/routers/feedback.py` — **NEW** `POST /api/v1/dossiers/{id}/feedback`, `GET /api/v1/feedback/stats`
  - `app/schemas/feedback.py` — **NEW** `FeedbackCreate`, `FeedbackOut`, `FeedbackStats`
  - `app/services/feedback_service.py` — **NEW** persist `AgentFeedback`; embed negative feedback into Chroma `feedback_lessons`
  - `app/services/memory/retriever.py` — retrieve feedback lessons before planner phase
  - `app/services/orchestrator/planner.py` — inject retrieved lessons into plan prompt
  - `app/routers/__init__.py` — register feedback router
  - `hdtv-ai-prototype/src/views/SplitViewWorkspace.vue` — 👍/👎 + comment UI
  - `hdtv-ai-prototype/src/services/api.js` — `submitFeedback`, `getFeedbackStats` exports
  - `test.sh` — T-20 verify cases
- **acceptance:** POST feedback → 201; row in `agent_feedbacks`; GET stats returns counts; negative feedback upserted to Chroma `feedback_lessons` (or degraded skip)
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

### T-21: Tool Chaining & Composition
- **deps:** T-17, T-18
- **files:**
  - `alembic/versions/008_tool_chaining.py` — add `output_mapping`, `chains_to` JSONB columns on `tool_configs`
  - `app/models/entities.py` — extend `ToolConfig` with `output_mapping`, `chains_to`
  - `app/services/orchestrator/executor.py` — after tool A: map output fields → tool B input per `output_mapping` / `chains_to`
  - `scripts/seed.py` — seed chain: `EcoOcrExtract` → `LegalGraphRAG` (`extracted_text` → `query`)
  - `test.sh` — T-21 verify cases
- **acceptance:** Seeded chain config exists; executor passes OCR output to LegalGraphRAG without LLM re-filling query; audit logs show both tools with linked inputs
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

### T-22: Human-in-the-Loop (HITL)
- **deps:** T-19
- **files:**
  - `app/models/entities.py` — **NEW** `AgentClarification` (`dossier_id`, `task_id`, `question`, `options` JSONB, `status`, `answer`)
  - `alembic/versions/009_agent_clarifications.py` — migration
  - `app/routers/clarifications.py` — **NEW** `GET /clarifications/pending`, `POST /clarifications/{id}/answer`
  - `app/services/orchestrator/react_agent.py` — pause on low confidence / tool conflict; resume after answer (Celery task stores state in DB)
  - `app/services/pubsub.py` — WS event `clarification_needed`
  - `hdtv-ai-prototype/src/views/SplitViewWorkspace.vue` — clarification modal
  - `hdtv-ai-prototype/src/services/api.js` — `getPendingClarifications`, `answerClarification` exports
  - `test.sh` — T-22 verify cases
- **acceptance:** Clarification row created on conflict trigger; POST answer → status `answered`; appraisal resumes and completes; WS emits `clarification_needed`
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

### T-23: Role-Based Agent Profiles
- **deps:** T-17, T-16
- **files:**
  - `app/services/orchestrator/prompts/__init__.py` — **NEW** package
  - `app/services/orchestrator/prompts/hdtv_leader.py` — concise, risk-first system prompt
  - `app/services/orchestrator/prompts/dept_head.py` — checklist detail, supplement recommendations
  - `app/services/orchestrator/prompts/specialist.py` — full technical report
  - `app/services/orchestrator/prompts/admin.py` — full audit, no summarization
  - `app/services/orchestrator/prompt_builder.py` — **NEW** `build_system_prompt(role, tools, preferences)`
  - `app/routers/dossiers.py` — `POST /dossiers/{id}/appraise` accepts optional `user_id` query/body
  - `app/services/orchestrator/react_agent.py` — use `prompt_builder` instead of hardcoded prompt
  - `test.sh` — T-23 verify cases
- **acceptance:** Appraise with `user_id=1` (hdtv_leader) vs `user_id=4` (specialist) produces different `resolution_md` length/focus; role prompt files exist for all 4 roles
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

### T-24: Agent Intelligence Dashboard
- **deps:** T-17, T-19, T-20
- **files:**
  - `app/routers/meta.py` — `GET /api/v1/agent/metrics` (plan_revision_rate, critic_rejection_rate, feedback_count, memory_retrieval_count)
  - `app/services/agent_metrics_service.py` — **NEW** aggregate from `agent_plans`, `appraisal_results.critic_verdict`, `agent_feedbacks`, audit logs
  - `app/schemas/meta.py` — `AgentMetricsOut`
  - `hdtv-ai-prototype/src/views/SystemAdminView.vue` — new tab "Agent Intelligence" with metrics cards
  - `hdtv-ai-prototype/src/stores/admin.js` — `fetchAgentMetrics()` action
  - `hdtv-ai-prototype/src/services/api.js` — `getAgentMetrics` export
  - `test.sh` — T-24 verify cases
- **acceptance:** GET `/agent/metrics` returns JSON with `plan_revision_rate`, `critic_rejection_rate`, `feedback_total`; Admin tab renders without error
- **verify_cmd:** `npm run build` in hdtv-ai-prototype && `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

#### T-15 → T-24 Dependency Graph

| Task | Blocked by | Unlocks |
|------|------------|---------|
| T-15 | T-08, T-14 | T-16, T-17, T-20 |
| T-16 | T-15 | T-17, T-23 |
| T-17 | T-15, T-16 | T-18, T-19, T-20, T-21, T-23, T-24 |
| T-18 | T-17 | T-21 |
| T-19 | T-17 | T-22, T-24 |
| T-20 | T-15, T-17 | T-24 |
| T-21 | T-17, T-18 | — |
| T-22 | T-19 | — |
| T-23 | T-17, T-16 | — |
| T-24 | T-17, T-19, T-20 | Level 4 complete |

---

## Code Quality Pass (session 15)

- **status:** DONE
- **scope:** Cross-cutting quality review of all T-01 → T-24 code
- **fixes applied:**
  1. `tasks.py` — removed double-newline formatting artifact
  2. `react_agent.py` — `eval()` hardened: replaced bare `{"__builtins__": {}}` with `_eval_rule_expression()` using an explicit whitelist (`len`, `any`, `all`, `sum`, `min`, `max`, `bool`, `int`, `str`, `list`, `dict`, pre-computed `failed`/`passed`/`failed_tools`)
  3. `memory/retriever.py` — `import httpx` + `from app.services.memory.vector_store import ...` moved out of function body to module top level
  4. `tools/base.py`, `meta_service.py` — `is_active == True` replaced with `.is_(True)` (proper SQLAlchemy boolean comparison)
  5. `orchestrator/helpers.py` + callers — `build_check()` was `async` with no awaits; converted to sync; removed spurious `await` in `executor.py` and `react_agent.py`
  6. `services/llm_client.py` — added `max_retries=2` loop for transient network errors (`TransportError`, `TimeoutException`); fallback response extracted to module-level constant `_LLM_FALLBACK_RESPONSE`
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh` (file-based checks all pass)

---

## Phase 9 — Agent Infrastructure: Tooling, Security, Observability, Network Resilience

> **Mục tiêu:** Xây dựng "tay chân" hạ tầng cho Agent — MCP nâng cao, RAG pipeline tự động, sandboxing cứng, circuit breaker LLM, observability LLMOps.
> **Thứ tự ưu tiên:** T-25 → T-29 (không bao gồm CI/CD — sẽ làm riêng).
> **Platform context:** Alpine VM 192.168.157.10; hdtv-ai-platform chạy trong `docker-compose.hdtv.yml`; observability stack (Prometheus + Grafana + Loki + Jaeger + Alertmanager) đã deploy tại `platform/composition/docker-compose.observability.yml`; Traefik làm edge reverse proxy.

---

### T-25: LLM Circuit Breaker & Gemini Key Rotation Round-Robin
- **deps:** T-17, T-24
- **priority:** P1 — unblocks mọi thứ, ngăn agent kẹt infinite loop
- **problem:** `llm_router.py` đã có fallback Gemini ↔ local nhưng thiếu: (1) circuit breaker khi agent loop không kết thúc; (2) Gemini key rotation chỉ là round-robin toàn cục không reset sau lỗi; (3) không có absolute timeout toàn bộ appraisal task.
- **files:**
  - `app/core/circuit_breaker.py` — **NEW** `CircuitBreaker` class: states CLOSED/OPEN/HALF_OPEN, failure threshold (5 trong 60s), cooldown 30s; thread-safe dùng `asyncio.Lock`
  - `app/services/llm_router.py` — wrap `_call_gemini` + `_call_local_llm` với `CircuitBreaker` instances riêng; `_next_gemini_key()` upgrade: skip keys đang trong cooldown sau 429/403; emit `LLM_CALLS` label `status="circuit_open"` khi trip
  - `app/core/config.py` — thêm: `llm_circuit_failure_threshold: int = 5`, `llm_circuit_cooldown_s: int = 30`, `appraisal_max_duration_s: int = 300`
  - `app/workers/tasks.py` — wrap `run_appraisal()` trong `asyncio.wait_for(appraisal_max_duration_s)` — nếu timeout → set dossier status `needs_revision`, emit WS event `timeout`
  - `app/core/metrics.py` — thêm counter: `hdtv_llm_circuit_trips_total` (labels: backend, role), `hdtv_appraisal_timeouts_total`
  - `test.sh` — T-25 verify cases: circuit breaker file exists; config keys present; metrics counter names in metrics.py
- **acceptance:** `CircuitBreaker` class tồn tại; `llm_router.py` import và sử dụng nó; appraisal task có `asyncio.wait_for`; metric `hdtv_llm_circuit_trips_total` khai báo trong `metrics.py`
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

---

### T-26: Sandbox Audit Log + Docker Ephemeral Executor Upgrade
- **deps:** T-25
- **priority:** P1 — bảo mật, mọi lệnh Agent chạy phải có trace
- **problem:** `sandbox_executor.py` đã có process-level sandbox tốt nhưng: (1) không ghi vào `AiAuditLog` → không thể trace lại Agent chạy lệnh gì; (2) comment "upgrade Docker sau này" chưa implement; (3) `SandboxShell` tool chưa emit Prometheus metrics.
- **files:**
  - `app/services/tools/sandbox_executor.py` — trong `run_shell_command()` và `run_python_snippet()`: sau khi có result, gọi `_emit_sandbox_audit()` helper; thêm Prometheus counter `hdtv_sandbox_executions_total` (labels: type=shell|python, status=success|blocked|timeout|error)
  - `app/services/tools/sandbox_executor.py` — thêm `_emit_sandbox_audit(command, result, task_id)` — ghi `AiAuditLog` row với `tool_name="SandboxShell"`, `inputs={"command": ...}`, `outputs=result.to_agent_dict()` dùng `async_session_factory`
  - `app/services/tools/docker_sandbox.py` — **NEW** `DockerSandboxExecutor`: chạy `docker run --rm --network none --memory 64m --cpus 0.5 --read-only python:3.11-alpine python -c "<code>"` qua `asyncio.create_subprocess_exec`; timeout cứng 15s; fallback sang `run_python_snippet` nếu Docker socket không available
  - `app/core/config.py` — thêm: `sandbox_use_docker: bool = False` (default False — an toàn cho dev), `sandbox_docker_image: str = "python:3.11-alpine"`, `sandbox_docker_memory: str = "64m"`, `sandbox_docker_timeout_s: int = 15`
  - `app/core/metrics.py` — thêm: `hdtv_sandbox_executions_total` counter (type, status)
  - `docker-compose.hdtv.yml` — thêm `worker` service: mount `/var/run/docker.sock:/var/run/docker.sock:ro` khi `SANDBOX_USE_DOCKER=true` (conditional comment)
  - `test.sh` — T-26 verify cases: docker_sandbox.py exists; sandbox metrics in metrics.py; AiAuditLog write in sandbox_executor
- **acceptance:** `docker_sandbox.py` tồn tại với `DockerSandboxExecutor`; `sandbox_executor.py` gọi `_emit_sandbox_audit`; metric `hdtv_sandbox_executions_total` khai báo; config `sandbox_use_docker` có trong `Settings`
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

---

### T-27: RAG Data Ingestion Pipeline (Celery + Embedding Worker)
- **deps:** T-15, T-16, T-25
- **priority:** P2 — RAG hiện static, cần tự động ingest tài liệu mới
- **problem:** Chroma collections hiện chỉ được upsert thủ công trong `seed.py` và theo từng bước agent. Chưa có pipeline tự động: (1) thu thập tài liệu mới; (2) chunk + embed; (3) quản lý context buffer size; (4) `CONTEXT_TRUNCATIONS` metric trong `context_manager.py` chưa emit.
- **files:**
  - `app/workers/rag_pipeline.py` — **NEW** Celery task `ingest_legal_documents(source_dir)`: đọc file `.txt`/`.md` từ `/opt/rag-docs/` (volume), chunk bằng sliding window (512 tokens, overlap 64), upsert từng chunk vào Chroma collection `legal_docs` với metadata `{source, chunk_idx, ingested_at}`; task chạy mỗi 6h qua Celery beat
  - `app/workers/rag_pipeline.py` — Celery task `cleanup_stale_embeddings()`: xoá docs Chroma có `ingested_at` > 30 ngày; chạy mỗi ngày lúc 02:00
  - `app/core/context_manager.py` — trong `fit_messages()`: emit `CONTEXT_TRUNCATIONS.labels(model=...).inc()` mỗi khi cắt messages (hiện counter khai báo trong metrics.py nhưng chưa được gọi từ đây)
  - `app/services/memory/vector_store.py` — thêm function `upsert_legal_doc(doc_id, text, metadata)` và `query_legal_docs(query, top_k)` dùng collection `legal_docs`
  - `app/services/tools/legal_rag.py` — cập nhật `legal_graph_rag()`: sau khi query LEGAL_FALLBACK, thêm fallback query Chroma `legal_docs` collection (T-27 docs ingest); merge kết quả, deduplicate by doc_id
  - `app/workers/celeryconfig.py` (hoặc `celery_app.py`) — thêm Celery beat schedule: `ingest_legal_documents` mỗi 6h, `cleanup_stale_embeddings` daily 02:00
  - `docker-compose.hdtv.yml` — `worker` service: thêm volume mount `hdtv_rag_docs:/opt/rag-docs` để agent và pipeline chia sẻ cùng nguồn tài liệu; thêm service `beat` (memory 64m) cho Celery beat scheduler
  - `app/core/config.py` — thêm: `rag_docs_dir: str = "/opt/rag-docs"`, `rag_chunk_size_tokens: int = 512`, `rag_chunk_overlap_tokens: int = 64`, `rag_legal_collection: str = "legal_docs"`, `rag_stale_days: int = 30`
  - `test.sh` — T-27 verify cases: rag_pipeline.py exists; celery beat schedule configured; legal_rag updated; context_manager emits truncation metric
- **acceptance:** `rag_pipeline.py` tồn tại với 2 Celery tasks; `context_manager.py` emit `CONTEXT_TRUNCATIONS`; `legal_rag.py` query Chroma `legal_docs`; Celery beat schedule có `ingest_legal_documents`; volume `hdtv_rag_docs` trong docker-compose
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

---

### T-28: Observability LLMOps — HDTV Alerts + Grafana Dashboard + OTel Tracing
- **deps:** T-25, T-26
- **priority:** P1
- **status:** DONE

---

### T-29: MCP Streamable HTTP (SSE) + Tool Output Schema Validation
- **deps:** T-25, T-26
- **priority:** P2
- **status:** DONE

---

## Phase 9 Dependency Graph

| Task | Blocked by | Unlocks | Priority |
|------|------------|---------|----------|
| T-25 | T-17, T-24 | T-26, T-27, T-28, T-29 | P1 |
| T-26 | T-25 | T-28 | P1 |
| T-27 | T-15, T-16, T-25 | — | P2 |
| T-28 | T-25, T-26 | — | P1 |
| T-29 | T-25, T-26 | — | P2 |

**Thứ tự thực hiện:** T-25 → T-26 → T-28 (song song với T-27) → T-29 → T-30

---

### T-30: Execution Harness — Tool Contract, Per-tool Timeout, Retry & Audit Correlation
- **deps:** T-25, T-26
- **priority:** P1 — hoàn thiện tầng dispatcher giữa Agent và Tools trước khi scale số lượng tools
- **problem:** Execution harness hiện tại (`executor.py` + `base.py` + `batch_executor.py`) thiếu 5 yếu tố cốt lõi:
  1. **Input validation tại dispatch** — `execute_tool()` nhận `dict` tự do, không validate schema trước khi gọi. Agent hallucinate sai field → tool crash, không rõ lỗi từ đâu.
  2. **Per-tool timeout** — chỉ `sandbox_executor` có timeout riêng; `ErpBudgetCheck`, `LegalGraphRAG` v.v. gọi Gemini qua `execute_tool()` không có guard → nếu Gemini treo, step treo vô thời hạn bên trong `execute_plan_steps()`.
  3. **Retry tại harness** — `batch_executor.py` không retry. Tool fail = agent mất observation ngay, phải chờ critic re-run. Cần 1 retry với backoff ngắn (2s) cho transient errors trước khi kết luận fail.
  4. **Error taxonomy** — `execute_tool()` trả `{"error": str(exc)}` flat, không phân biệt: `transient` (retry được), `bad_input` (không retry, sửa input), `tool_unavailable` (fallback). Agent không có đủ thông tin để tự quyết định.
  5. **Audit correlation** — `AiAuditLog` hiện không lưu `plan_step_id` → không thể correlate từ `agent_plans.plan_json` → audit row cụ thể → trace span.
  6. **`app/tools/handlers/` rỗng** — thư mục tồn tại nhưng chưa dùng; không có separation giữa "tool handler logic" và "business mock logic".
  7. **Celery beat service thiếu** — `docker-compose.hdtv.yml` không có `worker --beat` container riêng → T-27 RAG pipeline schedule không chạy được.
- **files:**
  - `app/services/tools/base.py` — trong `execute_tool()`: thêm `_validate_tool_input(name, params)` gọi trước fn(); nếu fail trả `{"error": "...", "error_type": "bad_input", "hint": "..."}` ngay không gọi fn; thêm `asyncio.wait_for(fn(params), timeout=tool_timeout)` với default `tool_execution_timeout_s`; bắt `asyncio.TimeoutError` → trả `{"error": "timeout", "error_type": "transient"}`
  - `app/services/tools/base.py` — thêm `_TOOL_INPUT_REQUIRED_FIELDS: dict[str, list[str]]` mapping tool_name → required keys (vd: `"ErpBudgetCheck": ["dossier_id", "doc_no"]`); `_validate_tool_input()` check required fields + type hints cơ bản (int/str)
  - `app/services/tools/base.py` — export `ToolErrorType` enum: `TRANSIENT | BAD_INPUT | UNAVAILABLE | UNKNOWN`; `execute_tool()` attach `error_type` vào mọi error response
  - `app/services/tools/batch_executor.py` — thêm `max_retries: int = 1`, `retry_backoff_s: float = 2.0` params vào `execute_parallel()`; nếu output có `error_type == "transient"` → retry sau backoff; nếu `bad_input` hoặc `max_retries` hết → trả lại error kèm `retried=True` flag
  - `app/services/orchestrator/executor.py` — trong `_run_tool_with_audit()`: retry logic tương tự cho sequential steps; `AiAuditLog` thêm field: gọi `session.add(AiAuditLog(..., plan_step_id=plan_step.get("id"), error_type=output.get("error_type")))` — cần migration
  - `app/models/entities.py` — `AiAuditLog`: thêm column `plan_step_id: Mapped[str | None]` (String 64, nullable, index=True) và `error_type: Mapped[str | None]` (String 32, nullable)
  - `alembic/versions/010_audit_log_harness.py` — **NEW** migration: ADD COLUMN `plan_step_id VARCHAR(64)`, `error_type VARCHAR(32)` ON `ai_audit_logs`
  - `app/core/config.py` — thêm: `tool_execution_timeout_s: int = 30` (per-tool timeout, default 30s — bằng llm_timeout/4), `tool_max_retries: int = 1`, `tool_retry_backoff_s: float = 2.0`
  - `app/core/metrics.py` — thêm: `hdtv_tool_retries_total` counter (labels: tool_name, error_type), `hdtv_tool_timeouts_total` counter (labels: tool_name), `hdtv_tool_input_validation_errors_total` counter (labels: tool_name)
  - `app/tools/handlers/__init__.py` — **NEW** package init; comment về convention: mỗi tool phức tạp nên có handler riêng tại đây
  - `app/tools/handlers/erp_handler.py` — **NEW** thin wrapper: `ErpBudgetHandler`, `ErpInventoryHandler` classes với `validate_input()` + `execute()` methods; `tools/base.py` gọi handler thay vì gọi trực tiếp `_erp_budget_check()` — pattern để scale khi tools nhiều hơn
  - `docker-compose.hdtv.yml` — thêm service `beat`: image giống `worker`, command `celery -A app.workers.celery_app beat --loglevel=info --scheduler celery.beat:PersistentScheduler`; depends_on redis; memory limit 64m — cần để T-27 RAG pipeline schedule chạy được
  - `test.sh` — T-30 verify cases: `_validate_tool_input` function exists in base.py; `ToolErrorType` defined; `plan_step_id` column in AiAuditLog entity; migration 010 file exists; beat service in docker-compose; retry logic in batch_executor; tool timeout config key; handler __init__ exists
- **acceptance:**
  - `execute_tool()` có `asyncio.wait_for` với `tool_execution_timeout_s`
  - `_validate_tool_input()` tồn tại và được gọi trước `fn(params)`
  - `ToolErrorType` enum khai báo với ≥3 values
  - `AiAuditLog` entity có column `plan_step_id` + `error_type`
  - Migration `010_audit_log_harness.py` tồn tại
  - `batch_executor.py` có retry logic (grep `retry` hoặc `max_retries`)
  - Metrics `hdtv_tool_retries_total`, `hdtv_tool_timeouts_total` khai báo trong `metrics.py`
  - `docker-compose.hdtv.yml` có service `beat`
  - `app/tools/handlers/__init__.py` tồn tại
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

---

## Phase 9 Dependency Graph (updated)

| Task | Blocked by | Unlocks | Priority |
|------|------------|---------|----------|
| T-25 | T-17, T-24 | T-26, T-27, T-28, T-29, T-30 | P1 |
| T-26 | T-25 | T-28, T-30 | P1 |
| T-27 | T-15, T-16, T-25 | — | P2 |
| T-28 | T-25, T-26 | — | P1 |
| T-29 | T-25, T-26 | — | P2 |
| T-30 | T-25, T-26 | — | P1 |

**Thứ tự thực hiện:** T-25 → T-26 → (T-28, T-30 song song) → (T-27, T-29 song song)

---

## Phase 10 — Production Professionalization: LLM Node, Observability, Token Management

> **Mục tiêu:** Chuyển đổi hệ thống từ dev demo sang production-ready — nâng cấp LLM node với TLS/observability, hoàn thiện observability stack, thêm dashboard quản lý token/keys.
> **Platform context:** Alpine VM (core platform + HDTV) + Ubuntu LLM node; use Ansible để setup LLM node professionally.

---

### T-31: LLM Node Professionalization (Caddy + Metrics + Logs)
- **deps:** T-02
- **priority:** P1 — bảo vệ LLM endpoint, có observability cho LLM node
- **problem:** LLM node hiện tại expose HTTP 8080 trực tiếp, không TLS, không metrics, không log centralize.
- **files:**
  - `ansible-ubuntu/roles/llm_node/tasks/main.yml` — cài đặt Caddy (reverse proxy TLS), Prometheus Node Exporter, Promtail (log shipping)
  - `ansible-ubuntu/roles/llm_node/templates/docker-compose.llm.yml.j2` — thêm node-exporter, promtail services; đổi llama-server listen trên 127.0.0.1:8081, Caddy expose :8080 (HTTP) và :8443 (HTTPS self-signed)
  - `ansible-ubuntu/roles/llm_node/templates/Caddyfile.j2` — cấu hình Caddy reverse proxy, TLS self-signed, rate limit
  - `ansible-ubuntu/roles/llm_node/defaults/main.yml` — thêm vars: llm_tls_enabled, llm_metrics_enabled, llm_log_shipping_enabled
  - `project_devops/platform/composition/docker-compose.observability.yml` — thêm scrape config cho LLM node (node-exporter + llama-server metrics nếu có)
- **acceptance:** Caddy chạy trên Ubuntu, reverse proxy đến llama-server; node-exporter expose metrics; promtail ship logs đến Alpine Loki; LLM endpoint vẫn reachable từ Alpine VM.
- **verify_cmd:** `./cli.sh ansible-deploy-llm && curl -sfk https://$ACER_HOST:8443/v1/models`
- **status:** DONE

---

### T-32: Observability Completeness Check & Alertmanager Setup
- **deps:** T-28
- **priority:** P1 — đảm bảo toàn bộ stack có observability đầy đủ
- **problem:** Chưa kiểm tra xem observability stack (Prometheus/Grafana/Loki/Alertmanager) đã đủ cover toàn bộ services chưa; Alertmanager chưa setup notification (Telegram/Slack).
- **files:**
  - `project_devops/platform/composition/docker-compose.observability.yml` — đảm bảo Alertmanager service có, thêm config notification
  - `project_devops/platform/config/prometheus/alertmanager.yml` — **NEW** file cấu hình Alertmanager receivers (Telegram dùng token từ .env)
  - `project_devops/platform/config/prometheus/alerts/hdtv_alerts.yml` — đảm bảo tất cả HDTV alerts có, thêm alerts cho LLM node
  - `cli.sh` — thêm lệnh `obs-alerts` để check alert status
- **acceptance:** Alertmanager running; all HDTV + LLM node alerts present; test alert firing (e.g., stop hdtv-api and wait for alert).
- **verify_cmd:** `./cli.sh obs-up && curl -sf http://localhost:9093/api/v2/alerts`
- **status:** DONE

---

### T-33: Token/API Keys Management Dashboard (Backend + FE)
- **deps:** T-30
- **priority:** P1 — quản lý các keys/tokens một cách professional, không để trong .env plaintext
- **problem**: Gemini keys, MCP API key, MinIO keys hiện tại lưu trong .env plaintext; không có UI để quản lý, rotate keys.
- **files:**
  - `app/models/entities.py` — **NEW** model `ApiKey` (id, name, key_type, key_prefix, hashed_key, is_active, created_by, created_at, last_used_at)
  - `alembic/versions/011_add_api_keys.py` — **NEW** migration
  - `app/core/config.py` — thay đổi cách đọc keys: ưu tiên đọc từ DB, fallback .env
  - `app/services/api_key_service.py` — **NEW** CRUD cho ApiKey, hash key bằng bcrypt, verify key
  - `app/routers/api_keys.py` — **NEW** endpoints: GET /api/v1/api-keys, POST /api/v1/api-keys, DELETE /api/v1/api-keys/{id}
  - `app/routers/__init__.py` — register api_keys router
  - `app/services/llm_router.py` — cập nhật `_next_gemini_key()` để lấy key từ DB thay vì .env
  - `hdtv-ai-prototype/src/views/SystemAdminView.vue` — thêm tab "API Keys Management"
  - `hdtv-ai-prototype/src/stores/admin.js` — thêm actions fetchApiKeys, createApiKey, deleteApiKey
  - `hdtv-ai-prototype/src/services/api.js` — thêm exports getApiKeys, createApiKey, deleteApiKey
  - `test.sh` — T-33 verify cases
- **acceptance:** ApiKey model exists; can create/delete keys via API; FE tab renders; llm_router uses DB keys; keys are hashed (không lưu plaintext trong DB).
- **verify_cmd:** `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status:** DONE

---

### T-34: HDTV Workflow Observability Dashboard (Grafana)
- **deps:** T-32
- **priority:** P2 — dashboard để thấy toàn bộ workflow appraisal diễn ra
- **problem:** Chưa có Grafana dashboard chuyên biệt để trace một appraisal từ đầu đến cuối (plan → steps → tools → result).
- **files:**
  - `project_devops/platform/config/grafana/provisioning/dashboards/hdtv_workflow.json` — **NEW** Grafana dashboard:
    - Panel: LLM calls per role (local vs Gemini)
    - Panel: Tool execution duration distribution
    - Panel: Appraisal status breakdown (pending/running/completed/failed)
    - Panel: Audit log feed (recent tool calls)
    - Panel: Circuit breaker status
  - `cli.sh` — thêm note về cách import dashboard
- **acceptance:** Dashboard exists in Grafana provisioning; all panels show data when running appraisals.
- **verify_cmd:** `open http://grafana.nano.platform/d/hdtv-workflow`
- **status:** DONE

---

### T-35: Backup Strategy (Automated)
- **deps:** T-31
- **priority:** P2 — đảm bảo dữ liệu không mất
- **problem**: Chưa có backup automated cho Postgres, MinIO, Chroma data.
- **files**:
  - `project_devops/apps/hdtv-ai-platform/scripts/backup.sh` — **NEW** script: backup Postgres (pg_dump), MinIO (mc mirror), Chroma (tar.gz); upload to local backup volume
  - `project_devops/platform/composition/docker-compose.hdtv.yml` — thêm service `backup` (cron container chạy backup.sh daily)
  - `cli.sh` — thêm lệnh `hdtv-backup` (run backup manually) và `hdtv-restore` (placeholder)
  - `ansible-ubuntu/roles/llm_node/tasks/main.yml` — thêm backup cho LLM model file (nếu cần)
- **acceptance**: Backup script runs without errors; backup files exist in volume; can restore Postgres from backup (test manually).
- **verify_cmd**: `./cli.sh hdtv-backup && ls -la /opt/platform/backups`
- **status**: DONE

---

### T-36: MCP Token Management & Audit
- **deps:** T-33
- **priority**: P2
- **problem**: MCP API key hiện tại chỉ single key; không có audit log cho MCP calls.
- **files**:
  - `app/models/entities.py` — thêm `mcp_call_id` vào `AiAuditLog` (nếu cần); hoặc **NEW** model `McpCallLog`
  - `app/routers/mcp.py` — thêm audit log cho mỗi MCP call; dùng ApiKey auth từ DB thay vì .env
  - `hdtv-ai-prototype/src/views/SystemAdminView.vue` — thêm tab "MCP Audit Logs"
- **acceptance**: Every MCP call is logged; MCP uses DB ApiKeys instead of .env single key.
- **verify_cmd**: `bash project_devops/apps/hdtv-ai-platform/test.sh`
- **status**: DONE

---

## Phase 10 Dependency Graph

| Task | Blocked by | Unlocks | Priority |
|------|------------|---------|----------|
| T-31 | T-02 | T-32 | P1 |
| T-32 | T-31, T-28 | T-34 | P1 |
| T-33 | T-30 | T-36 | P1 |
| T-34 | T-32 | — | P2 |
| T-35 | T-31 | — | P2 |
| T-36 | T-33 | — | P2 |

---

### T-37: LLM Node Teardown & Reset
- **deps**: T-02
- **priority**: P1 — reset LLM node về clean state (chỉ để lại SSH + Docker)
- **problem**: Khi test lỗi, cần xóa toàn bộ LLM stack (containers, volumes, dữ liệu) để cài lại từ đầu, mà không xóa base OS/SSH.
- **files**:
  - `project_devops/apps/ansible-ubuntu/teardown-llm.yml` — Ansible playbook để teardown LLM node
  - `cli.sh` — thêm lệnh `ansible-teardown-llm` và `ansible-teardown-full`
- **acceptance**:
  - Chạy `./cli.sh ansible-teardown-llm` → xóa containers/volumes/dữ liệu LLM node
  - Chạy `./cli.sh ansible-teardown-full` → full reset (xóa cả Docker)
  - Sau teardown, chạy `./cli.sh ansible-deploy-llm` → cài lại thành công
- **verify_cmd**: `./cli.sh ansible-teardown-llm && ./cli.sh ansible-deploy-llm && curl -sf http://$ACER_HOST:8080/v1/models`
- **status**: DONE

---

## Phase 10 Dependency Graph (updated)

| Task | Blocked by | Unlocks | Priority |
|------|------------|---------|----------|
| T-31 | T-02 | T-32 | P1 |
| T-32 | T-31, T-28 | T-34 | P1 |
| T-33 | T-30 | T-36 | P1 |
| T-34 | T-32 | — | P2 |
| T-35 | T-31 | — | P2 |
| T-36 | T-33 | — | P2 |
| T-37 | T-02 | T-31 (re-deploy) | P1 |

**Thứ tự thực hiện:** T-37 (nếu cần reset) → T-31 → T-32 → T-33 → (T-34, T-35, T-36 song song)
