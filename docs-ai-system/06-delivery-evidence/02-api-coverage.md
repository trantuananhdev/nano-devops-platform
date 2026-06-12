# API Coverage — 40+ Endpoints, All Verified

> **Audience:** CTO, CEO
> **Mục đích:** Danh sách đầy đủ API endpoints đã implement và verified — đây là deliverable cụ thể.

---

## Core Business APIs

| Endpoint | Method | Mô tả | Status |
|----------|--------|-------|--------|
| `/health` | GET | Health check | ✅ |
| `/dossiers` | GET | Danh sách hồ sơ (pagination) | ✅ |
| `/dossiers` | POST | Tạo hồ sơ mới (201/409 duplicate) | ✅ |
| `/dossiers/{id}` | GET | Chi tiết hồ sơ + appraisal result | ✅ |
| `/dossiers/{id}/appraise` | POST | Bắt đầu thẩm định (202 Accepted) | ✅ |
| `/dossiers/{id}/upload` | POST | Upload PDF lên MinIO | ✅ |
| `/dossiers/{id}/pdf-url` | GET | Presigned URL download PDF | ✅ |
| `/dossiers/{id}/feedback` | POST | Submit 👍/👎 feedback | ✅ |

## Search

| Endpoint | Method | Mô tả | Status |
|----------|--------|-------|--------|
| `/search?q=&risk=&status=` | GET | Full-text search (Meilisearch, degraded mode) | ✅ |

## Workflow (BPMN)

| Endpoint | Method | Mô tả | Status |
|----------|--------|-------|--------|
| `/workflows/{dossier_id}` | GET | Load BPMN XML từ DB | ✅ |
| `/workflows/{dossier_id}` | PUT | Save BPMN XML + audit log | ✅ |
| `/workflows` | GET | Danh sách tất cả diagrams | ✅ |

## Admin & Monitoring

| Endpoint | Method | Mô tả | Status |
|----------|--------|-------|--------|
| `/users` | GET | Danh sách users | ✅ |
| `/roles` | GET | Role definitions | ✅ |
| `/system-logs` | GET | System activity log | ✅ |
| `/audit-logs` | GET | AI tool call audit logs | ✅ |
| `/alerts` | GET | Open alerts | ✅ |
| `/alerts/{id}/resolve` | PATCH | Resolve alert | ✅ |
| `/feedback/stats` | GET | Aggregate feedback stats | ✅ |

## Meta / Dashboard

| Endpoint | Method | Mô tả | Status |
|----------|--------|-------|--------|
| `/dashboard/summary` | GET | KPIs: pending, high_risk, approved, alerts | ✅ |
| `/tools` | GET | Tool registry list | ✅ |
| `/knowledge-graph` | GET | Knowledge graph nodes + edges | ✅ |
| `/schedules` | GET | Celery beat schedules | ✅ |
| `/skills` | GET | Agent skill definitions | ✅ |
| `/checklist-template` | GET | Appraisal checklist template | ✅ |
| `/agent/metrics` | GET | Agent KPIs (revision_rate, rejection_rate...) | ✅ |

## User Preferences

| Endpoint | Method | Mô tả | Status |
|----------|--------|-------|--------|
| `/users/{id}/preferences` | GET | Get user preferences | ✅ |
| `/users/{id}/preferences` | PUT | Update user preferences | ✅ |

## HITL (Human-in-the-Loop)

| Endpoint | Method | Mô tả | Status |
|----------|--------|-------|--------|
| `/clarifications/pending` | GET | Pending HITL requests | ✅ |
| `/clarifications/{id}/answer` | POST | Answer + resume appraisal | ✅ |

## API Key Management

| Endpoint | Method | Mô tả | Status |
|----------|--------|-------|--------|
| `/api-keys` | GET | List API keys (type filter) | ✅ |
| `/api-keys` | POST | Create key (hashed, prefix visible) | ✅ |
| `/api-keys/{id}` | DELETE | Deactivate key | ✅ |

## MCP Server

| Endpoint | Method | Mô tả | Status |
|----------|--------|-------|--------|
| `/mcp/manifest` | GET | MCP server manifest | ✅ |
| `/mcp/tools/list` | POST | List tools with JSON schema | ✅ |
| `/mcp/tools/call` | POST | Sync tool call | ✅ |
| `/mcp/tools/call/stream` | POST | SSE streaming tool call | ✅ |
| `/mcp/audit-logs` | GET | MCP call audit logs | ✅ |
| `/mcp/health` | GET | MCP health check | ✅ |

## WebSocket

| Endpoint | Protocol | Events | Status |
|----------|----------|--------|--------|
| `/ws/appraisal/{id}` | WebSocket | 11 event types real-time | ✅ |

---

## Summary

```
Total endpoints:  40+ REST + 1 WebSocket
All verified:     test.sh + manual testing
API docs:         http://<VM_IP>:8000/docs (FastAPI auto-generated)
Response format:  Consistent JSON, standard HTTP status codes
Error format:     {"detail": "message"} — no stack traces in production
```
