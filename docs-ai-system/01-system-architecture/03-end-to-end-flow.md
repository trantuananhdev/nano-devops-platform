# End-to-End Flow — User đến Kết quả

> **Audience:** CTO, Solution Architect
> **Mục đích:** Full sequence diagram từ lúc user thao tác đến khi nhận kết quả thẩm định.

---

## Happy Path Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User as 👤 Cán bộ thẩm định
    participant FE as 🖥️ Vue.js Frontend
    participant API as ⚡ FastAPI
    participant WS as 🔌 WebSocket
    participant Redis as ⚡ Redis Queue
    participant Celery as ⚙️ Celery Worker
    participant Memory as 🔮 Agent Memory
    participant RAG as 📚 Legal RAG
    participant Planner as 🧠 Planner
    participant Executor as ⚙️ Executor
    participant Tools as 🔧 Tool Harness
    participant Reflector as 🪞 Reflector
    participant Critic as 🎯 Critic
    participant PG as 🗄️ PostgreSQL
    participant Chroma as 🔮 Chroma DB

    Note over User,Chroma: === PHASE 1: SUBMIT ===
    User->>FE: Mở giao diện thẩm định
    User->>FE: Upload PDF hồ sơ
    FE->>API: POST /dossiers/{id}/upload (multipart)
    API->>PG: Update pdf_url on dossier
    API-->>FE: 200 OK, presigned URL

    User->>FE: Bấm "Thẩm định"
    FE->>API: POST /dossiers/{id}/appraise
    API->>PG: Create AppraisalRecord (status: queued)
    API->>Redis: Enqueue appraisal task
    API-->>FE: 202 Accepted + {task_id, ws_url}
    FE->>WS: Connect WebSocket /ws/appraisal/{id}

    Note over User,Chroma: === PHASE 2: CONTEXT LOADING ===
    Celery->>WS: Emit "task_started"
    Celery->>Memory: retrieve_relevant_memories(dossier_id, query)
    Memory->>Chroma: Query agent-memories collection (top-k=5)
    Chroma-->>Memory: Relevant past observations
    Memory-->>Celery: Context chunks

    Celery->>Memory: retrieve_feedback_lessons()
    Memory->>Chroma: Query feedback-lessons collection
    Chroma-->>Memory: Learning from past mistakes
    Memory-->>Celery: Feedback lessons

    Celery->>RAG: query_legal_docs(dossier context)
    RAG->>Chroma: Query legal_docs collection
    Chroma-->>RAG: Relevant regulations & precedents
    RAG-->>Celery: Legal context

    Note over User,Chroma: === PHASE 3: PLANNING ===
    Celery->>Planner: create_plan(context + memory + legal)
    Planner->>API: POST llama-server /v1/chat (JSON mode)
    API-->>Planner: Structured plan JSON
    Planner-->>Celery: {goal, steps:[{id, tool, parallel_group}]}
    Celery->>PG: INSERT agent_plans (plan_json, revision=0)
    Celery->>WS: Emit "plan_created" {steps_count}

    Note over User,Chroma: === PHASE 4: EXECUTION (parallel batches) ===
    loop For each parallel_group in plan
        Celery->>Executor: execute_batch(tools_in_group)
        par Parallel tools in same group
            Executor->>Tools: ErpBudgetCheck({dossier_id, doc_no})
            Tools->>PG: INSERT ai_audit_logs (plan_step_id)
            Tools-->>Executor: {budget_status, amount}
        and
            Executor->>Tools: ErpInventoryCheck({dossier_id})
            Tools->>PG: INSERT ai_audit_logs
            Tools-->>Executor: {inventory_status}
        end
        Executor->>WS: Emit "tool_result" per tool
    end

    Note over User,Chroma: === PHASE 5: REFLECTION ===
    Celery->>Memory: upsert observations to Chroma
    Celery->>Reflector: reflect_on_results(observations)
    Reflector->>API: POST llama-server /v1/chat
    API-->>Reflector: sufficient | revise | escalate

    alt Verdict = revise (max 2 revisions)
        Reflector-->>Celery: {revised_steps}
        Celery->>WS: Emit "plan_revised"
        Celery->>Executor: Re-execute revised steps
    else Verdict = escalate (low confidence)
        Reflector-->>Celery: {escalate, reason}
        Celery->>PG: INSERT agent_clarifications
        Celery->>WS: Emit "clarification_needed" {question, options}
        User->>FE: Reads question, selects answer
        FE->>API: POST /clarifications/{id}/answer
        API->>Redis: Resume task with answer context
        Celery->>WS: Emit "clarification_answered"
    else Verdict = sufficient
        Reflector-->>Celery: proceed
    end

    Note over User,Chroma: === PHASE 6: QUALITY GATE ===
    Celery->>Critic: review_draft(report_md, checks, risk_level)
    Critic->>API: POST Gemini Flash (or llama fallback)
    API-->>Critic: {approved, issues, suggested_fixes}
    Celery->>PG: UPDATE appraisal_results (critic_verdict)
    Celery->>WS: Emit "critic_review" {approved, issues_count}

    alt Critic rejects (max 2 rejections)
        Celery->>Executor: Re-execute failed tool checks
        Celery->>Celery: Regenerate report section
    end

    Note over User,Chroma: === PHASE 7: FINALIZE ===
    Celery->>PG: INSERT appraisal_results (resolution_md, risk_level)
    Celery->>Memory: upsert final memory to Chroma
    Celery->>WS: Emit "appraisal_complete" {risk_level}
    FE->>User: Display final report + Risk badge

    Note over User,Chroma: === PHASE 8: FEEDBACK LOOP ===
    User->>FE: Submit 👍/👎 + comment
    FE->>API: POST /dossiers/{id}/feedback
    API->>PG: INSERT agent_feedbacks
    API->>Chroma: Upsert negative feedback to feedback-lessons
    Note right of Chroma: Agent học từ phản hồi này<br/>cho lần thẩm định tiếp theo
```

---

## Error paths

| Tình huống | Behavior |
|-----------|----------|
| LLM timeout (>300s) | `asyncio.wait_for` → task timeout → status `needs_revision` + WS `timeout` |
| Tool TRANSIENT error | Retry 1x với 2s backoff → nếu vẫn fail → `error_type: transient` trong audit log |
| Tool BAD_INPUT | Không retry, return `{error_type: bad_input, hint}` → Planner revise |
| Chroma unreachable | Degraded mode: fallback sang full PG scan (không 500) |
| Meilisearch down | `_degraded: true` trong search response (không 500) |
| Circuit breaker OPEN | LLM Router fails-over: Gemini → local hoặc local → rule-based fallback |
| Max revisions reached | Skip to Critic với current draft |
| Max critic rejections | Accept draft with `approved: false` in verdict |
