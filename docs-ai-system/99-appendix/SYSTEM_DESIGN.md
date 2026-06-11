# System Design: HDTV AI Platform

---

## 1. Overall Nano Platform Architecture
```mermaid
graph TB
    LLAMA[("llama-server")]
    CADDY["Caddy"]
    NODE_EXPORTER["node-exporter"]
    PROMTAIL["Promtail"]
    TRAEFIK["Traefik"]
    PROMETHEUS["Prometheus"]
    GRAFANA["Grafana"]
    LOKI["Loki"]
    JAEGER["Jaeger"]
    ALERTMANAGER["Alertmanager"]
    HDTV_PG[("HDTV Postgres")]
    HDTV_REDIS[("HDTV Redis")]
    HDTV_CHROMA[("Chroma DB")]
    HDTV_MEILI[("Meilisearch")]
    HDTV_MINIO[("MinIO")]
    HDTV_API["FastAPI Backend"]
    HDTV_WORKER["Celery Worker"]
    HDTV_BEAT["Celery Beat"]
    HDTV_FE["HDTV Frontend"]
    USER["End Users"]

    CADDY --> LLAMA

    USER --> TRAEFIK
    TRAEFIK --> HDTV_FE
    TRAEFIK --> HDTV_API
    TRAEFIK --> GRAFANA
    TRAEFIK --> PROMETHEUS

    HDTV_API --> HDTV_PG
    HDTV_API --> HDTV_REDIS
    HDTV_API --> HDTV_CHROMA
    HDTV_API --> HDTV_MEILI
    HDTV_API --> HDTV_MINIO
    HDTV_WORKER --> HDTV_PG
    HDTV_WORKER --> HDTV_REDIS
    HDTV_WORKER --> HDTV_CHROMA
    HDTV_WORKER --> HDTV_MINIO
    HDTV_BEAT --> HDTV_REDIS
    HDTV_BEAT --> HDTV_CHROMA

    HDTV_API --> CADDY

    NODE_EXPORTER --> PROMETHEUS
    PROMTAIL --> LOKI
    PROMETHEUS --> CADDY
    PROMETHEUS --> HDTV_API
    PROMETHEUS --> ALERTMANAGER
    ALERTMANAGER --> USER
    GRAFANA --> PROMETHEUS
    GRAFANA --> LOKI
    GRAFANA --> JAEGER
```

---

## 2. Detailed HDTV AI System Design
```mermaid
graph TB
    FE_APP["HDTV React App"]
    FE_WS["WebSocket Client"]
    API_BUSINESS["HDTV Business API"]
    API_MCP["MCP Server"]
    API_LLM_ROUTER["LLM Router"]
    API_EXEC_HARNESS["Execution Harness"]
    PLANNER["Planner Agent"]
    EXECUTOR["Executor Agent"]
    REFLECTOR["Reflector Agent"]
    CRITIC["Critic Agent"]
    PG["HDTV Postgres"]
    REDIS["HDTV Redis"]
    CHROMA["Chroma DB"]
    MEILI["Meilisearch"]
    MINIO["MinIO"]
    CELERY_WORKER["Celery Worker"]
    CELERY_BEAT["Celery Beat"]

    FE_APP --> API_BUSINESS
    FE_APP --> API_MCP
    FE_APP <--> FE_WS
    FE_WS <--> API_BUSINESS
    API_BUSINESS --> API_LLM_ROUTER
    API_BUSINESS --> API_EXEC_HARNESS
    API_MCP --> API_EXEC_HARNESS
    API_LLM_ROUTER --> PLANNER
    API_LLM_ROUTER --> EXECUTOR
    API_LLM_ROUTER --> REFLECTOR
    API_LLM_ROUTER --> CRITIC
    API_EXEC_HARNESS --> EXECUTOR
    API_BUSINESS --> PG
    API_BUSINESS --> REDIS
    API_BUSINESS --> CHROMA
    API_BUSINESS --> MEILI
    API_BUSINESS --> MINIO
    CELERY_WORKER --> PG
    CELERY_WORKER --> REDIS
    CELERY_WORKER --> CHROMA
    CELERY_WORKER --> MINIO
    CELERY_BEAT --> REDIS
    CELERY_BEAT --> CHROMA
```

### 2.1 Key HDTV AI Components
| Component | Purpose | Details |
|-----------|---------|---------|
| **LLM Router** | Routes calls to right LLM backend | - Ubuntu llama-server (Gemma 4) → Planner/Executor/Reflector<br/>- Gemini Flash → Legal/Financial/Critic/Tool Mock<br/>- Circuit Breaker (Open/Closed/Half-Open)<br/>- Gemini API Key Rotation + Cooldown |
| **Execution Harness** | Validates, runs, and retries tools | - Input Validation (required fields + types)<br/>- Per-tool Timeout (30s)<br/>- Retry TRANSIENT Errors (1x, 2s backoff)<br/>- Error Taxonomy (TRANSIENT/BAD_INPUT/UNAVAILABLE/UNKNOWN)<br/>- DB-configured Fallback Responses |
| **MCP Server** | Exposes tools to external AI agents | - GET /mcp/manifest<br/>- POST /mcp/tools/list<br/>- POST /mcp/tools/call (sync)<br/>- POST /mcp/tools/call/stream (SSE)<br/>- GET /mcp/audit-logs<br/>- GET /mcp/health<br/>- X-MCP-API-Key Auth (DB + .env fallback) |
| **Agentic Agents** | Plan, execute, reflect, criticize | 1. Planner → Creates execution plan<br/>2. Executor → Runs parallel/chained tools<br/>3. Reflector → Analyzes observations<br/>4. Critic → Validates final report |
| **Audit Logs** | Tracks everything | - ai_audit_logs: tool calls with plan_step_id + error_type<br/>- mcp_call_logs: MCP server calls with api_key_id |

---

## 3. HDTV AI Full Workflow
```mermaid
sequenceDiagram
    autonumber
    actor User
    participant FE as HDTV Frontend
    participant API as FastAPI Backend
    participant WS as WebSocket
    participant Celery as Celery Worker
    participant Beat as Celery Beat
    participant PG as HDTV Postgres
    participant Redis as HDTV Redis
    participant Chroma as Chroma DB
    participant LLM as LLM Router
    participant Tools as Execution Harness
    participant Memory as Agent Memory
    participant RAG as Legal RAG
    participant Feedback as Feedback Lessons
    participant MCP as MCP Server

    User->>FE: Opens Appraisal UI
    FE->>API: POST /api/v1/dossiers/{id}/appraise
    API->>PG: Create Appraisal Record
    API->>Celery: Enqueue Appraisal Task
    API->>FE: 202 Accepted + WebSocket ID

    Celery->>WS: Send "task_started" Event

    Celery->>Memory: Get Agent Memory (Chroma)
    Memory-->>Celery: Previous Thoughts & Observations
    Celery->>Feedback: Get Feedback Lessons
    Feedback-->>Celery: Learning from Past Mistakes
    Celery->>RAG: Query Legal Docs
    RAG-->>Celery: Relevant Regulations & Precedents

    Celery->>LLM: Call Planner Agent (JSON Mode)
    LLM-->>Celery: Structured Execution Plan
    Celery->>PG: Save Agent Plan
    Celery->>WS: Send "plan_created" Event

    loop For Each Parallel Tool Batch
        Celery->>Tools: Execute Parallel Tools
        Tools->>PG: Log ai_audit_logs (plan_step_id)
        Tools->>PG: Update Plan Step Status
        Tools->>WS: Send "tool_executing" / "tool_result" Events
    end

    Celery->>Memory: Update Agent Memory
    Celery->>LLM: Call Reflector Agent
    LLM-->>Celery: Reflection & Next Steps

    alt Clarification Required
        Celery->>PG: Create Clarification Request
        Celery->>WS: Send "clarification_needed" Event
        User->>FE: Submits Clarification Answer
        FE->>API: POST /api/v1/clarifications/{id}/answer
        API->>Celery: Resume Appraisal Task
        Celery->>WS: Send "task_resumed" Event
    end

    Celery->>LLM: Call Critic Agent
    LLM-->>Celery: Verdict (Approved / Needs Revision / Escalate)
    Celery->>PG: Save Critic Verdict
    Celery->>WS: Send "critic_review" Event

    alt Verdict = Approved
        Celery->>PG: Save Final Appraisal Result
        Celery->>WS: Send "appraisal_complete" Event
        FE->>User: Display Final Report
        User->>FE: Submits Feedback
        FE->>API: POST /api/v1/dossiers/{id}/feedback
        API->>PG: Save Feedback
        API->>Feedback: Upsert Feedback Lessons to Chroma
    else Verdict = Needs Revision
        Celery->>LLM: Re-run Planner with Revision Instructions
    else Verdict = Escalate
        Celery->>WS: Send "escalation_required" Event
        FE->>User: Notify of Escalation
    end

    loop Every 6 Hours
        Beat->>RAG: Ingest New Legal Docs to Chroma
        RAG->>PG: Log ai_audit_logs
    end

    User->>FE: Admin → MCP Audit Logs
    FE->>MCP: GET /api/v1/mcp/audit-logs
    MCP->>PG: Query mcp_call_logs
    PG-->>MCP: Recent MCP Calls
    MCP-->>FE: Display Audit Logs
```

---

## Topology Constraints (Strictly Followed)
✅ **2-Node Setup**:
1. Ubuntu Node → ONLY LLM (Gemma 4) + Caddy + node-exporter + Promtail
2. Alpine VM → Everything else

✅ **LLM Over HTTP Only**: No embedded LLM

✅ **HDTV Has Dedicated Resources**: Own Postgres, Redis, Chroma, Meilisearch, MinIO

✅ **All Tool Calls Audited**: Every tool call logged with `plan_step_id` and `error_type`
