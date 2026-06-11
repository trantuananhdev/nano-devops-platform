# Model Context Protocol (MCP) Server

## Tổng quan

HDTV implements the **full Model Context Protocol (MCP)** spec, making our tools available to any MCP-compatible agent (Claude Desktop, custom agents, etc.).

- **File:** `app/routers/mcp.py`
- **Prefix:** `/mcp`
- **Version:** 1.2.0

## Endpoints

| Endpoint | Method | Mô tả |
|----------|--------|-------|
| `/mcp/manifest` | GET | Server manifest (capabilities, info) |
| `/mcp/tools/list` | POST | List tools with JSON schemas |
| `/mcp/tools/call` | POST | Synchronous tool call |
| `/mcp/tools/call/stream` | POST | **SSE streaming tool call** |
| `/mcp/health` | GET | Health check |
| `/mcp/audit-logs` | GET | Audit logs (admin) |

## Authentication

- **Header:** `X-MCP-API-Key`
- **Auth Flow:**
  1. Check `api_keys` table (hashed, expirable, active)
  2. Fallback to `.env` variable `MCP_API_KEY`
  3. Dev mode: No key required (if not configured)

## Tool Registry

Tools are defined in:
- **Static Registry:** `STATIC_TOOL_IMPLS` in `app/services/tools/base.py`
- **DB Tools:** `ToolConfig` table (active/inactive, priority)

## Audit Logs

All tool calls are logged to `mcp_call_logs`:
- `api_key_id`
- `tool_name`
- `inputs`
- `outputs`
- `execution_ms`
- `is_error`
- `is_streaming`

## Output Validation

Tools have required output schema defined in `_TOOL_OUTPUT_SCHEMAS`. Incomplete outputs are annotated with `output_incomplete` flag.

## Quick Start (MCP Client)

```http
POST /mcp/tools/call HTTP/1.1
Host: hdtv.nano.platform
X-MCP-API-Key: your-key-here
Content-Type: application/json

{
  "name": "LegalGraphRAG",
  "arguments": {
    "query": "Quy định về thẩm định hồ sơ"
  }
}
```
