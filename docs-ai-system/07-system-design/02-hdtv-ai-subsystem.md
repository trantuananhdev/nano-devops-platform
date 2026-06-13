# HDTV-AI Subsystem — L2 System Design

> **Tầng L2: Subsystem AI — từ API request đến appraisal result**
> **Audience:** Backend Lead, AI Engineer, Senior Dev
> **Cập nhật:** 2026-06-13

---

## Request Lifecycle — Full Flow

```
HTTP POST /appraisals/{dossier_id}/run
        │
        ▼
┌─────────────────────────────────────────────────────────────────┐
│  FastAPI Router (appraisals.py)                                  │
│  - Auth check (JWT → UserRole)                                   │
│  - Fetch Dossier + Tools from DB                                │
│  - Emit WS "appraisal_started" event                            │
└──────────────────────┬──────────────────────────────────────────┘
                       │  await or Celery.delay()
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  AI Orchestrator (orchestrator.py)                               │
│                                                                  │
│  1. MEMORY RETRIEVAL                                             │
│     retrieve_relevant_memories(dossier_id, query)               │
│     retrieve_cross_dossier_memories(unit, risk_level)           │
│     retrieve_feedback_lessons(unit)                             │
│                    │                                             │
│  2. PLAN                                                         │
│     create_plan(dossier, tools, memory_ctx, feedback_lessons)   │
│     → ExecutionPlan {goal, steps[], max_revisions}              │
│                    │                                             │
│  3. EXECUTE                                                      │
│     _build_execution_batches() → topological sort               │
│     asyncio.gather(parallel_group tools)                        │
│     Each step: ToolExecutor.execute(tool_name, input)           │
│                    │                                             │
│  4. REFLECT                                                      │
│     reflect(plan, observations) → ReflectionResult              │
│     Verdict: sufficient | revise | escalate                     │
│     if revise and revision < max_revisions → goto 2             │
│                    │                                             │
│  5. SUMMARIZE                                                    │
│     summarize(observations, dossier) → Markdown report          │
│                    │                                             │
│  6. CRITIC                                                       │
│     critic_review(report, checks) → CriticVerdict               │
│     if rejected → re-summarize (1 retry)                        │
│                    │                                             │
│  7. SAVE + EMIT                                                  │
│     Save AppraisalResult to PostgreSQL                          │
│     Publish WS "appraisal_complete" event                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Subsystem Components Map

```
hdtv-api process
├── app/
│   ├── routers/
│   │   ├── appraisals.py          ← HTTP endpoints (run, status, result)
│   │   ├── ws.py                  ← WebSocket connection handler
│   │   ├── dossiers.py            ← CRUD + status transitions
│   │   ├── clarifications.py      ← HITL pause/resume
│   │   └── ...
│   │
│   ├── services/
│   │   ├── orchestrator/          ← AI Orchestrator (CORE)
│   │   │   ├── orchestrator.py    ← Main Plan→Execute→Reflect→Critic loop
│   │   │   ├── planner.py         ← LLM planning + fallback
│   │   │   ├── executor.py        ← Parallel tool execution
│   │   │   ├── reflector.py       ← LLM reflection
│   │   │   ├── critic.py          ← LLM quality gate
│   │   │   ├── summarizer.py      ← LLM summary → report
│   │   │   ├── helpers.py         ← build_check() + confidence
│   │   │   ├── prompt_builder.py  ← Role-specific prompts
│   │   │   └── types.py           ← ExecutionPlan, ReflectionResult, etc.
│   │   │
│   │   ├── llm_router.py          ← AgentRole → backend routing + circuit breaker
│   │   ├── circuit_breaker.py     ← CLOSED/OPEN/HALF_OPEN per backend
│   │   │
│   │   ├── tools/                 ← 8 tool implementations
│   │   │   ├── legal_graph_rag.py
│   │   │   ├── erp_budget.py
│   │   │   ├── erp_inventory.py
│   │   │   ├── technical_check.py
│   │   │   ├── procurement_check.py
│   │   │   ├── doffice_lookup.py
│   │   │   ├── pmis_check.py
│   │   │   └── eco_ocr.py
│   │   │
│   │   ├── memory/                ← Memory hierarchy
│   │   │   ├── retriever.py       ← Composite scoring retrieval
│   │   │   └── vector_store.py    ← Chroma HTTP client
│   │   │
│   │   └── clarification_service.py  ← HITL pause/resume
│   │
│   ├── core/
│   │   ├── context_manager.py     ← Priority-based context eviction
│   │   ├── config.py              ← Settings (pydantic)
│   │   └── metrics.py             ← Prometheus counters/histograms
│   │
│   └── models/
│       └── entities.py            ← All SQLAlchemy models
```

---

## LLM Router — 9 Roles, 2 Backends

```
                    ┌─────────────────────────────────┐
                    │         LLM Router               │
                    │                                  │
  AgentRole ──────►│  PLANNER     ──────────────────► llama.cpp (Node 2)
  (per call)       │  EXECUTOR                        gemma-4-8b-it
                   │  REFLECTOR                       :8080/completion
                   │  SUMMARY                         context: 8192 tokens
                   │                                  │
                   │  LEGAL       ──────────────────► Gemini API (Cloud)
                   │  FINANCIAL                       gemini-2.5-flash
                   │  OCR                             context: 1M tokens
                   │  CRITIC                          │
                   │  TOOL_MOCK   ──────────────────► Gemini API
                   └─────────────────────────────────┘
                              │
                    Circuit Breaker per backend:
                    CLOSED (healthy)
                      │ failure_count >= threshold
                    OPEN (blocking, wait reset_timeout)
                      │ after timeout
                    HALF_OPEN (probe 1 request)
                      │ success
                    CLOSED
```

**Tại sao split PLANNER/EXECUTOR vs LEGAL/CRITIC?**

Local LLM (gemma) phù hợp với:
- Structured JSON output (plan, reflection) — ít cần kiến thức rộng
- Vietnamese context management — đã instruction-tuned

Gemini phù hợp với:
- Legal reasoning — cần knowledge base rộng
- OCR + multimodal — Gemini native image support
- Critic — cần reasoning phức tạp cross-reference

---

## Data Models (simplified)

```python
# Core entities (app/models/entities.py)

Dossier
  id, doc_no, title, unit, status (11 values), risk_level
  pdf_url, pdf_text, created_by, assigned_to
  created_at, updated_at

AppraisalResult  
  dossier_id, session_id, overall_risk, report_md, resolution_md
  checks: dict {"items": [{"tool", "status", "score", "confidence"}]}
  critic_verdict: dict {"approved", "confidence", "notes"}
  created_at

AgentMemory (short-term, per dossier)
  dossier_id, session_id, step, action, tool_name, thought, observation
  created_at

AiAuditLog (immutable trail)
  dossier_id, session_id, plan_step_id, tool_name
  inputs: dict, outputs: dict, execution_ms, error
  created_at

AgentFeedback (HITL learning)
  dossier_id, user_id, feedback_type (approve/reject/adjust)
  comment, created_at
  → async: stored in Chroma hdtv_feedback_lessons collection
```

---

## WebSocket Event Protocol

```json
// Server → Client events
{"type": "appraisal_started",     "data": {"dossier_id": 1, "session_id": "..."}}
{"type": "step_completed",        "data": {"tool": "LegalGraphRAG", "status": "pass"}}
{"type": "stream_chunk",          "data": {"text": "Kết quả thẩm định..."}}
{"type": "clarification_requested","data": {"question": "...", "clarification_id": 5}}
{"type": "appraisal_complete",    "data": {"dossier_id": 1, "overall_risk": "medium"}}
{"type": "notification_new",      "data": {"notification_id": 10, "title": "..."}}
{"type": "alert_triggered",       "data": {"alert_id": 3, "severity": "high"}}

// Client → Server
{"type": "subscribe",             "data": {"dossier_id": 1}}
{"type": "chat_message",          "data": {"message": "..."}}
```
