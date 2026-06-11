# HDTV AI Platform - CTO Design Overview

---

## Executive Summary
The HDTV AI Platform combines **system software engineering best practices** with **modern agentic AI patterns**, resulting in a production-ready, scalable, resilient, and intelligent system for dossier appraisal. This document explains the core design thinking behind each component.

---

## Core Design Principles

### 1. **System Software First**
We built the system like any enterprise-grade software:
- **Observability**: Full metrics, logs, tracing stack (Prometheus, Loki, Jaeger, Grafana)
- **Resilience**: Circuit breakers, retries, fallbacks, degraded mode
- **Security**: API keys, hashing, Docker sandbox, rate limiting
- **Scalability**: Async tasks, parallel execution, Celery workers
- **Maintainability**: Clear separation of concerns, audit logs, monitoring

### 2. **Agentic AI Second**
We layered intelligent agentic patterns on top of the solid system foundation:
- **ReAct Loop**: Plan → Execute → Reflect → Critic
- **Memory Hierarchy**: Short-term (session) + Long-term (cross-session) + Feedback learning
- **Role-based Specialization**: Different agents for different tasks
- **Human-in-the-loop**: Clarification requests when low confidence
- **Tool Use**: Structured tool calls with validation
- **Self-correction**: Critic reviews draft reports

---

## Component Deep Dive

### 1. **Frontend → Backend Flow**
- **Vue.js Frontend**: Clean UI with virtual scrolling, global search, lazy loading, infinite scroll
- **FastAPI Backend**: Async API with WebSocket for real-time updates
- **Celery Workers**: Background task processing for appraisals
- **Celery Beat**: Scheduled tasks (legal doc ingestion every 6 hours)
- **Design Thinking**: Separate UI from async processing, keep API responsive with WebSocket for updates

### 2. **Agent Orchestrator**
- **Planner Agent**: Creates structured execution plan (JSON mode to reduce hallucinations)
- **Executor Agent**: Runs parallel tool batches for efficiency
- **Reflector Agent**: Analyzes results and decides next steps
- **Critic Agent**: Reviews draft reports and suggests revisions
- **Design Thinking**: Break down complex appraisal into manageable steps, use parallelism for performance, add self-correction for quality

### 3. **LLM Router**
- **Local Backend (Ubuntu llama-server)**: Planner/Executor/Reflector/Summary (low latency, no network dependency)
- **Remote Backend (Gemini Flash API)**: Legal/Financial/OCR/Critic/Tool_Mock (domain knowledge, high accuracy)
- **Circuit Breakers**: Protect against repeated failures
- **Key Rotation**: Load balance + cooldown on 429s
- **Design Thinking**: Optimize cost and performance by routing tasks to appropriate backend, add resilience against failures

### 4. **Tool Execution Harness**
- **Input Validation**: Required fields, type checking
- **Timeout**: Per-tool timeouts (default 30s)
- **Retry**: Retry TRANSIENT errors (1x, 2s backoff)
- **Fallback**: DB-configured fallback responses
- **Audit**: Log all tool calls to `ai_audit_logs`
- **Design Thinking**: Make tool calls safe, reliable, and auditable

### 5. **Agent Memory System**
- **Short-term (PostgreSQL)**: Session-specific thoughts/actions
- **Long-term (Chroma DB)**: Cross-session memories with embeddings
- **Feedback Lessons (Chroma DB)**: Learn from past user feedback
- **User Preferences (PostgreSQL)**: Personalize agent behavior
- **Degraded Mode**: Fallback to PostgreSQL if Chroma is down
- **Design Thinking**: Enable agent to learn from past experiences, personalize to user, and stay resilient

### 6. **MCP Server**
- **Full MCP Spec**: Expose tools to any MCP-compatible agent
- **Auth**: X-MCP-API-Key (DB + .env fallback)
- **Audit**: Log all MCP calls to `mcp_call_logs`
- **Design Thinking**: Make system extensible, allow integration with external agents

---

## Topology Constraints (Strictly Followed)
✅ **2-Node Setup**:
1. Ubuntu Node → ONLY LLM (Gemma 4) + Caddy + node-exporter + Promtail
2. Alpine VM → Everything else

✅ **LLM Over HTTP Only**: No embedded LLM

✅ **HDTV Has Dedicated Resources**: Own Postgres, Redis, Chroma, Meilisearch, MinIO

✅ **All Tool Calls Audited**: Every tool call logged with `plan_step_id` and `error_type`

---

## Why This Works
This design gives us:
- **Performance**: Parallel tool execution, local LLM for planning, virtual scrolling
- **Resilience**: Circuit breakers, retries, fallbacks, degraded mode
- **Scalability**: Async tasks, Celery workers
- **Intelligence**: ReAct loop, memory, self-correction, human-in-the-loop
- **Observability**: Full metrics, logs, tracing stack
- **Extensibility**: MCP server for external agents
- **Cost Efficiency**: Local + remote LLM routing, key rotation
