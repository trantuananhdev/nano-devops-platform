# Quick Reference for HDTV AI

## File Locations

| Feature | File/Folder |
|---------|-------------|
| MCP Server | `app/routers/mcp.py` |
| Planner | `app/services/orchestrator/planner.py` |
| Executor | `app/services/orchestrator/executor.py` |
| Critic | `app/services/orchestrator/critic.py` |
| Memory Retriever | `app/services/memory/retriever.py` |
| Vector Store | `app/services/memory/vector_store.py` |
| Tool Base | `app/services/tools/base.py` |
| LLM Router | `app/services/llm_router.py` |
| Circuit Breaker | `app/core/circuit_breaker.py` |
| Rate Limiter | `app/core/rate_limiter.py` |
| Docker Compose | `project_devops/apps/hdtv-ai-platform/docker-compose.hdtv.yml` |
| AI CRM Pipeline | `project_devops/apps/ai-crm-pipeline/` |

## Key Tables (Postgres)

| Table | Purpose |
|-------|---------|
| `dossiers` | Hồ sơ cần thẩm định |
| `agent_memory` | Agent short-term memory |
| `agent_feedback` | User feedback |
| `agent_plan` | Execution plans |
| `ai_audit_logs` | All tool calls |
| `mcp_call_logs` | MCP server calls |
| `api_keys` | API keys for auth |
| `clarifications` | Human-in-the-loop |
| `tool_config` | Tool configs & fallbacks |

## Prometheus Metrics

| Metric | Purpose |
|--------|---------|
| `http_requests_total` | HTTP requests by endpoint/status |
| `http_request_duration_seconds` | HTTP latency |
| `tool_calls_total` | Tool calls (success/fail) |
| `tool_duration_seconds` | Tool execution time |
| `agent_plans_total` | Agent plans by verdict |
| `critic_rejections_total` | Critic rejections |
| `queue_depth` | Redis queue depth |

## Endpoints

| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/dossiers/{id}/appraise` | Start appraisal |
| `GET /api/v1/dossiers/{id}` | Get dossier |
| `GET /metrics` | Prometheus metrics |
| `GET /health` | Health check |
| `GET /mcp/manifest` | MCP manifest |
| `POST /mcp/tools/list` | MCP tools list |
| `POST /mcp/tools/call` | MCP tool call |
