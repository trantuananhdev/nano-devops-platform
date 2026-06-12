# HDTV AI System Diagram

> **Audience:** CTO
> **Mục đích:** Zoom vào HDTV AI Platform — internal components, data flows, và design decisions.

---

## Internal Architecture

```mermaid
graph TB
    subgraph "Frontend (Vue.js)"
        FE_APP["Vue.js App\n14 views, Pinia stores"]
        FE_WS["WebSocket Client\nReal-time updates"]
    end

    subgraph "Backend API Layer (FastAPI)"
        API_ROUTER["Request Router\n/api/v1/*"]
        API_WS["WebSocket Handler\n/ws/appraisal/{id}"]
        API_MCP["MCP Server\n/mcp/*"]
        API_KEYS["API Key Manager\n/api-keys/*"]
    end

    subgraph "AI Orchestration Layer"
        ORCHESTRATOR["Agent Orchestrator\nreact_agent.py"]
        PLANNER["🧠 Planner\nJSON execution plan"]
        EXECUTOR["⚙️ Executor\nParallel tool batches"]
        REFLECTOR["🪞 Reflector\nsufficient/revise/escalate"]
        CRITIC["🎯 Critic\nQuality gate"]
        PROMPT_BUILDER["Prompt Builder\nRole-based system prompts"]
    end

    subgraph "LLM Layer"
        LLM_ROUTER["LLM Router\nRole → Backend mapping"]
        CB_LOCAL["Circuit Breaker\nLocal"]
        CB_REMOTE["Circuit Breaker\nRemote"]
        LOCAL_LLM["🤖 llama-server\nGemma 4 (Ubuntu node)"]
        REMOTE_LLM["☁️ Gemini Flash\n(internet — pilot)"]
    end

    subgraph "Tool Execution Layer"
        HARNESS["Execution Harness\nValidate→Timeout→Retry→Audit"]
        TOOLS["Tool Registry\n7 tools"]
        SANDBOX["Docker Sandbox\nIsolated execution"]
    end

    subgraph "Memory & Knowledge Layer"
        STM["Short-term Memory\nPostgreSQL (session)"]
        LTM["Long-term Memory\nChroma (cross-session)"]
        FEEDBACK["Feedback Lessons\nChroma (learning)"]
        PREFS["User Preferences\nPostgreSQL"]
        RAG["Legal RAG\nChroma legal_docs"]
    end

    subgraph "Data Stores"
        PG[("PostgreSQL")]
        REDIS[("Redis")]
        CHROMA[("Chroma DB")]
        MEILI[("Meilisearch")]
        MINIO[("MinIO")]
    end

    FE_APP <-->|REST| API_ROUTER
    FE_APP <-->|SSE/WS| FE_WS
    FE_WS <-->|WS| API_WS

    API_ROUTER -->|Enqueue| REDIS
    REDIS -->|Dequeue| ORCHESTRATOR

    ORCHESTRATOR --> PLANNER & EXECUTOR & REFLECTOR & CRITIC
    ORCHESTRATOR --> PROMPT_BUILDER
    ORCHESTRATOR --> STM & LTM & FEEDBACK & PREFS & RAG

    PLANNER & EXECUTOR & REFLECTOR & CRITIC --> LLM_ROUTER
    LLM_ROUTER --> CB_LOCAL & CB_REMOTE
    CB_LOCAL --> LOCAL_LLM
    CB_REMOTE --> REMOTE_LLM

    EXECUTOR --> HARNESS
    API_MCP --> HARNESS
    HARNESS --> TOOLS
    TOOLS --> SANDBOX

    STM --> PG
    LTM --> CHROMA
    FEEDBACK --> CHROMA
    PREFS --> PG
    RAG --> CHROMA

    API_ROUTER --> PG & MEILI & MINIO & CHROMA
    ORCHESTRATOR --> PG & REDIS
```

---

## Component Responsibilities

| Component | Trách nhiệm | File |
|-----------|------------|------|
| **Agent Orchestrator** | Điều phối toàn bộ Agent loop, emit WS events | `orchestrator/react_agent.py` |
| **Planner** | Tạo execution plan dạng JSON có parallel_group | `orchestrator/planner.py` |
| **Executor** | Chạy tool batches song song, chain tool output | `orchestrator/executor.py` |
| **Reflector** | Đánh giá kết quả, quyết định revise/escalate | `orchestrator/reflector.py` |
| **Critic** | Quality gate cuối: approve/reject/suggest fixes | `orchestrator/critic.py` |
| **LLM Router** | Route role → backend, circuit breaker, key rotation | `services/llm_router.py` |
| **Execution Harness** | Validate input, timeout, retry, error taxonomy | `services/tools/base.py` |
| **MCP Server** | Standard protocol cho external AI agents | `routers/mcp.py` |
| **Prompt Builder** | Role-based system prompts (4 roles) | `orchestrator/prompt_builder.py` |

---

## Data Flow: Appraisal Request

```
1. POST /api/v1/dossiers/{id}/appraise
   └─ FastAPI: Create AppraisalRecord in PG
   └─ FastAPI: Enqueue task to Redis
   └─ FastAPI: Return 202 + WebSocket URL
                    ↓
2. Celery picks up task
   └─ Retrieve memories from Chroma (top-k relevant)
   └─ Retrieve feedback lessons from Chroma
   └─ Retrieve legal docs from Chroma (RAG)
   └─ Build system prompt (role-based)
                    ↓
3. Planner Agent → llama-server
   └─ Returns JSON plan: [{id, tool, parallel_group, depends_on}]
   └─ Save to agent_plans table
   └─ Emit WS: "plan_created"
                    ↓
4. Executor runs plan
   └─ Group tools by parallel_group
   └─ asyncio.gather for each parallel batch
   └─ Each tool: validate → timeout(30s) → retry(1x) → audit log
   └─ Chain: EcoOcrExtract.extracted_text → LegalGraphRAG.query
   └─ Emit WS: "tool_executing", "tool_result" per tool
                    ↓
5. Reflector Agent → llama-server
   └─ Returns: sufficient | revise | escalate
   └─ If revise: re-plan with revision instructions (max 2x)
   └─ If escalate: create AgentClarification, emit WS: "clarification_needed"
                    ↓
6. Critic Agent → Gemini Flash (or llama-server fallback)
   └─ Returns: {approved, issues, suggested_fixes}
   └─ Save critic_verdict to AppraisalResult
   └─ Emit WS: "critic_review"
                    ↓
7. Finalize
   └─ Save AppraisalResult to PG
   └─ Update agent memory in Chroma
   └─ Re-index Meilisearch
   └─ Emit WS: "appraisal_complete"
```

---

## WebSocket Events

| Event | Trigger | Payload |
|-------|---------|---------|
| `task_started` | Celery picks up task | `{dossier_id, task_id}` |
| `plan_created` | Planner returns plan | `{steps_count, parallel_groups}` |
| `plan_revised` | Reflector triggers revision | `{revision, reason}` |
| `tool_executing` | Before each tool call | `{tool_name, plan_step_id}` |
| `tool_result` | After each tool call | `{tool_name, status, execution_ms}` |
| `clarification_needed` | HITL trigger | `{question, options[]}` |
| `clarification_answered` | User answers | `{answer}` |
| `critic_review` | Critic returns verdict | `{approved, issues_count}` |
| `appraisal_complete` | Final result saved | `{risk_level, resolution_md}` |
| `escalation_required` | Agent can't decide | `{reason}` |
| `timeout` | Task exceeds max duration | `{duration_s}` |
