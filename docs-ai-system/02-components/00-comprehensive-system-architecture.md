# Comprehensive HDTV AI Platform Architecture (System Software + Agentic AI)

---

## 1. Overall End-to-End Flow (FE → BE → MCP → LLM → Tools)

```mermaid
flowchart TD
    User -->|Use App| FE
    FE -->|API Calls / WebSocket| BE
    BE -->|Route Requests| Router

    Router -->|Business Logic| Business
    Router -->|MCP Requests| MCP_Server

    Business -->|Agent Orchestration| Orchestrator
    Orchestrator -->|Plan| Planner
    Orchestrator -->|Execute| Executor
    Orchestrator -->|Reflect| Reflector
    Orchestrator -->|Criticize| Critic

    Executor -->|Execute Tools| Harness
    Harness -->|Call Tools| Tools

    MCP_Server -->|Execute Tools| Harness

    Harness -->|Route LLM Calls| LLM_Router
    LLM_Router -->|Local Tasks| Local_LLM
    LLM_Router -->|Domain Tasks| Remote_LLM

    Tools -->|Query Data| DataLayer

    DataLayer -->|Persist| PG
    DataLayer -->|Cache/Queue| Redis
    DataLayer -->|Vector Search| Chroma
    DataLayer -->|Full-text Search| Meili
    DataLayer -->|File Storage| MinIO

    BE -->|Background Tasks| Celery
    BE -->|Scheduled Tasks| Beat

    FE -->|Real-time Updates| WS
    BE -->|Push Events| WS

    %% Observability
    BE -->|Metrics| Prometheus
    BE -->|Logs| Loki
    BE -->|Tracing| Jaeger
    Prometheus -->|Dashboards| Grafana
    Loki --> Grafana
    Jaeger --> Grafana

    %% Agent Memory
    Orchestrator -->|Read/Write Memory| Memory
    Memory --> PG
    Memory --> Chroma

    %% Feedback Loop
    User -->|Submit Feedback| FE
    FE -->|Save Feedback| BE
    BE -->|Upsert Lessons| Chroma

    %% Node Definitions
    User([End User])
    FE[HDTV Vue.js Frontend]
    BE[FastAPI Backend]
    Router[Request Router]
    Business[Business Logic Layer]
    Orchestrator[Agent Orchestrator]
    Planner[Planner Agent]
    Executor[Executor Agent]
    Reflector[Reflector Agent]
    Critic[Critic Agent]
    Harness[Tool Execution Harness]
    Tools[Tools Layer]
    MCP_Server[MCP Server]
    LLM_Router[LLM Router]
    Local_LLM[Ubuntu llama-server]
    Remote_LLM[Gemini Flash API]
    DataLayer[Data Layer]
    PG[(PostgreSQL)]
    Redis[(Redis)]
    Chroma[(Chroma DB)]
    Meili[(Meilisearch)]
    MinIO[(MinIO)]
    Celery[Celery Worker]
    Beat[Celery Beat]
    WS[WebSocket]
    Prometheus[(Prometheus)]
    Loki[(Loki)]
    Jaeger[(Jaeger)]
    Grafana[Grafana]
    Memory[Agent Memory System]

    %% Styling
    classDef frontend fill:#4CC9F0,stroke:#3A0CA3,stroke-width:2px;
    classDef backend fill:#4361EE,stroke:#3A0CA3,stroke-width:2px;
    classDef agentic fill:#7209B7,stroke:#3A0CA3,stroke-width:2px;
    classDef tools fill:#F72585,stroke:#3A0CA3,stroke-width:2px;
    classDef data fill:#3F37C9,stroke:#3A0CA3,stroke-width:2px;
    classDef observability fill:#4CC9F0,stroke:#3A0CA3,stroke-width:2px;
    classDef user fill:#F15BB5,stroke:#3A0CA3,stroke-width:2px;

    class User user;
    class FE,WS frontend;
    class BE,Router,Business,Harness backend;
    class Orchestrator,Planner,Executor,Reflector,Critic,Memory agentic;
    class MCP_Server,LLM_Router,Tools tools;
    class PG,Redis,Chroma,Meili,MinIO,Celery,Beat data;
    class Prometheus,Loki,Jaeger,Grafana observability;
```

---

## 2. Detailed Agentic Orchestrator Flow (Plan → Execute → Reflect → Critic)

```mermaid
sequenceDiagram
    participant User
    participant FE
    participant BE
    participant WS
    participant Celery
    participant Orchestrator
    participant Memory
    participant RAG
    participant Planner
    participant Executor
    participant Harness
    participant Tools
    participant Reflector
    participant Critic
    participant LLM_Router
    participant Local_LLM
    participant Remote_LLM
    participant PG
    participant Chroma

    User->>FE: Upload dossier + Start appraisal
    FE->>BE: POST /api/v1/dossiers/{id}/appraise
    BE->>PG: Create Appraisal & AgentMemory records
    BE->>Celery: Enqueue appraisal task
    BE->>FE: 202 Accepted + WebSocket ID
    Celery->>WS: task_started

    %% Step 1: Retrieve Context
    Celery->>Memory: Retrieve relevant memories
    Memory->>Chroma: Query agent-memories
    Chroma-->>Memory: Top-K relevant memories
    Memory-->>Celery: Context + past learnings

    Celery->>RAG: Retrieve legal precedents
    RAG->>Chroma: Query legal-docs
    Chroma-->>RAG: Relevant legal docs
    RAG-->>Celery: Legal context

    %% Step 2: Plan
    Celery->>Orchestrator: Initialize ReAct agent
    Orchestrator->>Planner: Create execution plan
    Planner->>LLM_Router: Route to PLANNER role
    LLM_Router->>Local_LLM: Call local Gemma 4
    Local_LLM-->>LLM_Router: Structured plan
    LLM_Router-->>Planner: Plan
    Planner-->>Orchestrator: Plan
    Orchestrator->>PG: Save plan
    Orchestrator->>WS: plan_created

    %% Step 3: Execute
    loop For each parallel tool batch
        Orchestrator->>Executor: Execute batch
        Executor->>Harness: Validate inputs
        Harness->>Tools: Execute tools
        Tools->>PG: Log ai_audit_logs
        Tools-->>Harness: Results
        Harness-->>Executor: Results
        Executor->>PG: Update plan step
        Executor->>WS: tool_executing / tool_result
    end

    %% Step 4: Reflect
    Orchestrator->>Reflector: Analyze results
    Reflector->>LLM_Router: Route to REFLECTOR role
    LLM_Router->>Local_LLM: Call local Gemma 4
    Local_LLM-->>LLM_Router: Reflection
    LLM_Router-->>Reflector: Reflection
    Reflector-->>Orchestrator: Reflection

    %% Step 5: Human-in-the-loop
    alt Low confidence
        Orchestrator->>PG: Create clarification
        Orchestrator->>WS: clarification_needed
        User->>FE: Submit answer
        FE->>BE: POST /api/v1/clarifications/{id}/answer
        BE->>Celery: Resume task
        Orchestrator->>WS: task_resumed
    end

    %% Step 6: Criticize
    Orchestrator->>Critic: Review draft report
    Critic->>LLM_Router: Route to CRITIC role
    LLM_Router->>Remote_LLM: Call Gemini Flash
    Remote_LLM-->>LLM_Router: Verdict
    LLM_Router-->>Critic: Verdict
    Critic-->>Orchestrator: Verdict
    Orchestrator->>PG: Save verdict
    Orchestrator->>WS: critic_review

    %% Step 7: Finalize
    alt Approved
        Orchestrator->>PG: Save final appraisal
        Orchestrator->>Memory: Upsert to agent-memories
        Orchestrator->>WS: appraisal_complete
        FE->>User: Show final report
        User->>FE: Submit feedback
        FE->>BE: POST /api/v1/dossiers/{id}/feedback
        BE->>PG: Save agent_feedback
        BE->>Chroma: Upsert to feedback-lessons
    else Needs Revision
        Orchestrator->>Planner: Re-plan
    else Escalate
        Orchestrator->>WS: escalation_required
        FE->>User: Notify escalation
    end
```

---

## 3. LLM Router Detailed Architecture (Key Rotation + Circuit Breakers)

```mermaid
flowchart TB
    Request --> Router

    Router --> Role_Map

    Role_Map -->|PLANNER| CB_Local
    Role_Map -->|EXECUTOR| CB_Local
    Role_Map -->|REFLECTOR| CB_Local
    Role_Map -->|SUMMARY| CB_Local
    Role_Map -->|LEGAL| CB_Remote
    Role_Map -->|FINANCIAL| CB_Remote
    Role_Map -->|OCR| CB_Remote
    Role_Map -->|CRITIC| CB_Remote
    Role_Map -->|TOOL_MOCK| CB_Remote

    CB_Local -->|CLOSED| Local
    CB_Local -->|OPEN| CB_Remote
    Local --->|Success| CB_Local
    Local --->|Failure| CB_Local

    CB_Remote -->|CLOSED| Key_Picker
    Key_Picker --> DB_Keys
    Key_Picker --> Env_Keys
    DB_Keys --> Cooldown
    Env_Keys --> Cooldown
    Cooldown -->|Pick key| Remote
    Remote --->|Success| Cooldown
    Remote --->|Rate Limit| Cooldown
    Cooldown -->|Add key to cooldown| Key_Picker
    Remote --->|Failure| CB_Remote
    CB_Remote -->|OPEN| CB_Local

    %% Node Definitions
    Request[LLM Request]
    Router[LLM Router]
    Role_Map{Role Mapping}
    DB_Keys[(PostgreSQL)]
    Env_Keys[Env Vars]
    Key_Picker[Key Picker]
    Cooldown[Cooldown Tracker]
    CB_Local[Circuit Breaker Local]
    CB_Remote[Circuit Breaker Remote]
    Local[Ubuntu llama-server]
    Remote[Gemini Flash API]

    %% Styling
    classDef router fill:#4361EE,stroke:#3A0CA3,stroke-width:2px;
    classDef keys fill:#4CC9F0,stroke:#3A0CA3,stroke-width:2px;
    classDef cb fill:#7209B7,stroke:#3A0CA3,stroke-width:2px;
    classDef backend fill:#3F37C9,stroke:#3A0CA3,stroke-width:2px;

    class Router,Role_Map router;
    class DB_Keys,Env_Keys,Key_Picker,Cooldown keys;
    class CB_Local,CB_Remote cb;
    class Local,Remote backend;
```

---

## 4. Tool Execution Harness (Validation + Timeout + Retry + Audit)

```mermaid
flowchart TD
    ToolCall --> Validator
    Validator -->|Valid| Timeout
    Validator -->|Invalid| Audit
    Audit --> Result

    Timeout -->|Set timeout| Retry
    Retry -->|Attempt 1| Executor
    Executor -->|Success| Audit
    Executor -->|TRANSIENT| Retry
    Retry -->|Attempt 2| Executor
    Executor -->|TRANSIENT 2| Fallback
    Executor -->|UNAVAILABLE| Fallback
    Executor -->|UNKNOWN| Fallback
    Fallback --> Audit
    Audit --> Result

    subgraph Tools
        T1[LegalGraphRAG]
        T2[ErpBudgetCheck]
        T3[ErpInventoryCheck]
        T4[DOfficeLookup]
        T5[PmisProjectCheck]
        T6[EcoOcrExtract]
        T7[SandboxShell]
    end

    Executor --> Tools

    %% Node Definitions
    ToolCall[Tool Call Request]
    Validator[Input Validator]
    Timeout[Timeout Manager]
    Retry[Retry Handler]
    Executor[Tool Executor]
    Fallback[Fallback Response]
    Audit[Audit Logger]
    Result[Return Result]

    %% Styling
    classDef harness fill:#4361EE,stroke:#3A0CA3,stroke-width:2px;
    classDef tools fill:#F72585,stroke:#3A0CA3,stroke-width:2px;

    class Validator,Timeout,Retry,Executor,Fallback,Audit harness;
    class T1,T2,T3,T4,T5,T6,T7 tools;
```

---

## 5. Agent Memory System (Short-term + Long-term + Feedback)

```mermaid
flowchart TB
    Orchestrator -->|Write| STM
    STM -->|Read| Orchestrator
    Orchestrator -->|Upsert| LTM
    LTM -->|Retrieve| Orchestrator
    Orchestrator -->|Upsert| Feedback
    Feedback -->|Retrieve| Orchestrator
    Orchestrator -->|Read| Preferences
    Preferences -->|Personalize| Orchestrator

    STM --> PG
    LTM --> Chroma
    Feedback --> Chroma
    Preferences --> PG

    %% Degraded Mode
    LTM --> Degraded
    Feedback --> Degraded
    Degraded{Chroma Available?}
    Degraded -->|No| PG

    %% Node Definitions
    Orchestrator[Agent Orchestrator]
    STM[Short-term Memory]
    LTM[Long-term Memory]
    Feedback[Feedback Lessons]
    Preferences[User Preferences]
    PG[(PostgreSQL)]
    Chroma[(Chroma DB)]

    %% Styling
    classDef orchestrator fill:#7209B7,stroke:#3A0CA3,stroke-width:2px;
    classDef memory fill:#3F37C9,stroke:#3A0CA3,stroke-width:2px;

    class Orchestrator orchestrator;
    class STM,LTM,Feedback,Preferences,PG,Chroma memory;
```

---

## 6. MCP Server Architecture (Auth + Tools + Audit)

```mermaid
flowchart TD
    Client --> Auth
    Auth -->|Valid Key| Manifest
    Auth -->|Valid Key| List
    Auth -->|Valid Key| CallSync
    Auth -->|Valid Key| CallStream
    Auth -->|Valid Key| AuditLogs
    Auth -->|Valid Key| Health

    Manifest --> Client
    List --> ToolRegistry
    ToolRegistry --> StaticTools
    ToolRegistry --> DBTools
    ToolRegistry --> Client

    CallSync --> Harness
    CallStream --> Harness
    Harness -->|Log| AuditDB
    Harness -->|Result| CallSync
    Harness -->|SSE| CallStream

    AuditLogs --> AuditDB
    AuditDB --> AuditLogs
    AuditLogs --> Client

    Health --> Client

    %% Node Definitions
    Client[MCP Client]
    Auth[Authentication]
    Manifest[GET /mcp/manifest]
    List[POST /mcp/tools/list]
    CallSync[POST /mcp/tools/call]
    CallStream[POST /mcp/tools/call/stream]
    AuditLogs[GET /mcp/audit-logs]
    Health[GET /mcp/health]
    ToolRegistry[Tool Registry]
    StaticTools[Static Tools]
    DBTools[DB Tools]
    Harness[Tool Execution Harness]
    AuditDB[(mcp_call_logs)]

    %% Styling
    classDef mcp fill:#4361EE,stroke:#3A0CA3,stroke-width:2px;
    classDef tools fill:#F72585,stroke:#3A0CA3,stroke-width:2px;
    classDef audit fill:#3F37C9,stroke:#3A0CA3,stroke-width:2px;

    class Auth,Manifest,List,CallSync,CallStream,AuditLogs,Health mcp;
    class ToolRegistry,StaticTools,DBTools,Harness tools;
    class AuditDB audit;
```

---

## 7. Key Design Principles (System Software + Agentic AI)

### System Software Principles
- Microservices-like Architecture: Separate concerns (API, workers, databases)
- Observability First: Metrics, logs, tracing (Prometheus, Loki, Jaeger, Grafana)
- Resilience: Circuit breakers, retries, fallbacks, degraded mode
- Security: API keys, hashing, Docker sandbox, rate limiting
- Performance: Virtual scrolling, parallel tool execution, caching

### Agentic AI Principles
- ReAct Loop: Plan → Execute → Reflect → Critic
- Memory Hierarchy: Short-term (session) + Long-term (cross-session) + Feedback learning
- Role-based Specialization: Different agents for different tasks
- Human-in-the-loop: Clarification requests when low confidence
- Tool Use: Structured tool calls with validation
- Self-correction: Critic reviews draft reports, suggests revisions

### Hybrid Strengths
- Best of Both Worlds: Combines software engineering best practices with modern agentic AI
- Cost Optimization: Local LLM for planning/execution, remote for domain knowledge
- Scalability: Async tasks, parallel execution, distributed workers
- Maintainability: Clear separation of concerns, audit logs, monitoring
