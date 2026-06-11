"""
MCP Server — Model Context Protocol (streamable-HTTP transport).

Spec: https://modelcontextprotocol.io/specification (2025-03-26)

T-29 additions:
  - POST /mcp/tools/call/stream — SSE streaming transport for long-running tools
  - _TOOL_OUTPUT_SCHEMAS — required output field validation per tool
  - _validate_tool_output() — called before returning result from mcp_call_tool
  - manifest capabilities: streaming.supported = True

T-36 additions:
  - _require_mcp_key() — upgraded to verify against DB api_keys (ApiKeyType.mcp)
    with fallback to .env MCP_API_KEY for zero-downtime migration
  - _log_mcp_call() — writes McpCallLog row after every /call and /call/stream
  - GET /mcp/audit-logs — list recent MCP calls (admin view)

Cài đặt lightweight: không dùng SDK nặng (mcp package), implement thuần FastAPI.
Hỗ trợ:
  - GET  /mcp/manifest              → server manifest (name, version, capabilities)
  - POST /mcp/tools/list            → danh sách tools với JSON schema input
  - POST /mcp/tools/call            → gọi một tool với params, trả result
  - POST /mcp/tools/call/stream     → SSE streaming (T-29)
  - GET  /mcp/health                → health check
  - GET  /mcp/audit-logs            → recent MCP call logs (T-36)

Security:
  - Header X-MCP-API-Key required — verified against DB api_keys then .env fallback
  - Tất cả input validated qua Pydantic trước khi đến execute_tool
  - Tool output luôn bọc trong MCP content envelope

Agent bên ngoài (như Claude desktop, custom MCP client) có thể kết nối vào đây
để gọi ErpBudgetCheck, LegalGraphRAG, v.v. mà không cần biết nội bộ FastAPI.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, AsyncGenerator

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.metrics import TOOL_CALLS, TOOL_DURATION
from app.services.tools.base import execute_tool, list_tools_dynamic

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/mcp", tags=["MCP"])


# ---------------------------------------------------------------------------
# T-36: Auth context — carries verified key info for audit logging
# ---------------------------------------------------------------------------

class _McpKeyContext:
    """Carries the API key identity resolved during auth."""

    __slots__ = ("key_id", "key_prefix", "raw_key")

    def __init__(self, key_id: int | None, key_prefix: str, raw_key: str) -> None:
        self.key_id = key_id
        self.key_prefix = key_prefix
        self.raw_key = raw_key


# ---------------------------------------------------------------------------
# Auth dependency — T-36: DB ApiKey verification with .env fallback
# ---------------------------------------------------------------------------

async def _require_mcp_key(x_mcp_api_key: str = Header(default="")) -> _McpKeyContext:
    """Validate X-MCP-API-Key header.

    Priority:
    1. Active mcp-type key in api_keys DB table
    2. .env MCP_API_KEY fallback (zero-downtime migration path)

    Returns _McpKeyContext with resolved key_id and prefix for audit logging.
    Raises HTTP 401 when key is required but invalid.
    """
    settings = get_settings()
    provided = x_mcp_api_key.strip()

    # ── Try DB verification first ────────────────────────────────────────────
    if provided:
        try:
            from app.core.database import async_session_factory
            from app.models.entities import ApiKeyType
            from app.services.api_key_service import verify_api_key
            from sqlalchemy import select
            from app.models.entities import ApiKey

            async with async_session_factory() as db:
                # Fast path: look up by prefix first to limit bcrypt checks
                stmt = (
                    select(ApiKey)
                    .where(ApiKey.key_type == ApiKeyType.mcp)
                    .where(ApiKey.is_active.is_(True))
                    .where(ApiKey.key_prefix == provided[:8])
                )
                rows = (await db.execute(stmt)).scalars().all()

                from app.services.api_key_service import _verify_hash
                for row in rows:
                    if _verify_hash(provided, row.hashed_key):
                        logger.debug("MCP auth: DB key id=%d prefix=%s", row.id, row.key_prefix)
                        return _McpKeyContext(
                            key_id=row.id,
                            key_prefix=row.key_prefix,
                            raw_key=provided,
                        )
        except Exception as exc:
            # DB unavailable — fall through to .env check
            logger.debug("MCP DB key lookup failed (%s), trying .env fallback", exc)

    # ── .env fallback ─────────────────────────────────────────────────────────
    expected = settings.mcp_api_key
    if expected:
        if provided == expected:
            prefix = provided[:8] if len(provided) >= 8 else provided
            return _McpKeyContext(key_id=None, key_prefix=prefix, raw_key=provided)
        # Key required (expected set) but doesn't match
        raise HTTPException(status_code=401, detail="Invalid MCP API key")

    # No key configured — open access (dev mode)
    return _McpKeyContext(key_id=None, key_prefix="open", raw_key="")


# ---------------------------------------------------------------------------
# T-36: Audit logging helper
# ---------------------------------------------------------------------------

async def _log_mcp_call(
    *,
    key_ctx: _McpKeyContext,
    tool_name: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
    is_error: bool,
    is_streaming: bool,
    execution_ms: int,
    output_incomplete: bool = False,
    missing_fields: list[str] | None = None,
) -> None:
    """Write a McpCallLog row — fire-and-forget, never raises.

    Called from both /call and /call/stream endpoints after execution.
    Uses a separate DB session to avoid interfering with request transaction.
    """
    try:
        from app.core.database import async_session_factory
        from app.models.entities import McpCallLog

        async with async_session_factory() as db:
            row = McpCallLog(
                api_key_id=key_ctx.key_id,
                api_key_prefix=key_ctx.key_prefix,
                tool_name=tool_name,
                inputs=inputs,
                outputs=outputs,
                is_error=is_error,
                is_streaming=is_streaming,
                execution_ms=execution_ms,
                output_incomplete=output_incomplete,
                missing_fields=missing_fields or [],
            )
            db.add(row)
            await db.commit()
    except Exception as exc:
        logger.warning("MCP audit log failed (non-fatal): %s", exc)


# ---------------------------------------------------------------------------
# T-29: Tool OUTPUT schemas — required fields per tool for validation
# ---------------------------------------------------------------------------

_TOOL_OUTPUT_SCHEMAS: dict[str, list[str]] = {
    "ErpBudgetCheck":    ["approved_budget", "exceeded"],
    "ErpInventoryCheck": ["available_quantity", "status"],
    "DOfficeLookup":     ["found", "doc_no"],
    "PmisProjectCheck":  ["project_status", "budget_remaining"],
    "LegalGraphRAG":     ["results"],
    "EcoOcrExtract":     ["extracted_text"],
}

_FIELD_HINTS: dict[str, str] = {
    "approved_budget":    "Cần trả về hạn mức ngân sách được phê duyệt (số tiền VNĐ)",
    "exceeded":           "Cần trả về boolean exceeded — ngân sách có bị vượt không",
    "available_quantity": "Cần trả về số lượng vật tư tồn kho",
    "status":             "Cần trả về trạng thái (available/partial/unavailable)",
    "found":              "Cần trả về boolean found — tìm thấy văn bản không",
    "doc_no":             "Cần trả về số văn bản tìm thấy",
    "project_status":     "Cần trả về trạng thái dự án (active/completed/suspended)",
    "budget_remaining":   "Cần trả về ngân sách còn lại của dự án",
    "results":            "Cần trả về danh sách kết quả tìm kiếm pháp lý",
    "extracted_text":     "Cần trả về văn bản OCR trích xuất từ PDF",
}


def _validate_tool_output(tool_name: str, result: dict[str, Any]) -> dict[str, Any]:
    """Validate tool output has required fields per _TOOL_OUTPUT_SCHEMAS.

    Non-blocking — annotates incomplete results for agent guidance rather than raising.
    """
    required_fields = _TOOL_OUTPUT_SCHEMAS.get(tool_name)
    if not required_fields:
        return result

    missing: list[str] = [f for f in required_fields if f not in result]
    if not missing:
        return result

    hints = [
        f"{field}: {_FIELD_HINTS.get(field, 'Required field missing')}"
        for field in missing
    ]
    logger.warning("MCP output validation: tool=%s missing=%s", tool_name, missing)
    return {
        **result,
        "output_incomplete": True,
        "missing_fields":    missing,
        "validation_hint":   f"Tool '{tool_name}' output missing: {', '.join(hints)}",
    }


# ---------------------------------------------------------------------------
# JSON Schema per tool (exposed to MCP clients via /tools/list)
# ---------------------------------------------------------------------------

_TOOL_INPUT_SCHEMAS: dict[str, dict[str, Any]] = {
    "ErpBudgetCheck": {
        "type": "object",
        "required": ["dossier_id", "doc_no"],
        "properties": {
            "dossier_id": {"type": "integer", "description": "ID hồ sơ thẩm định"},
            "doc_no":     {"type": "string",  "description": "Số hiệu văn bản (vd: 123/TTr-B02)"},
            "title":      {"type": "string",  "description": "Tiêu đề tờ trình"},
            "query":      {"type": "string",  "description": "Truy vấn cụ thể cho ERP"},
        },
    },
    "ErpInventoryCheck": {
        "type": "object",
        "required": ["dossier_id", "doc_no"],
        "properties": {
            "dossier_id":    {"type": "integer"},
            "doc_no":        {"type": "string"},
            "material_code": {"type": "string", "description": "Mã vật tư cần kiểm tra"},
        },
    },
    "DOfficeLookup": {
        "type": "object",
        "required": ["dossier_id", "doc_no"],
        "properties": {
            "dossier_id": {"type": "integer"},
            "doc_no":     {"type": "string"},
            "title":      {"type": "string"},
        },
    },
    "PmisProjectCheck": {
        "type": "object",
        "required": ["dossier_id", "doc_no"],
        "properties": {
            "dossier_id":   {"type": "integer"},
            "doc_no":       {"type": "string"},
            "project_code": {"type": "string", "description": "Mã dự án PMIS"},
        },
    },
    "LegalGraphRAG": {
        "type": "object",
        "required": ["query"],
        "properties": {
            "query":      {"type": "string", "description": "Câu hỏi pháp lý cần tra cứu"},
            "dossier_id": {"type": "integer"},
            "doc_no":     {"type": "string"},
        },
    },
    "EcoOcrExtract": {
        "type": "object",
        "required": ["dossier_id"],
        "properties": {
            "dossier_id": {"type": "integer"},
            "pdf_url":    {"type": "string", "description": "URL file PDF cần trích xuất"},
        },
    },
}


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class McpToolCallRequest(BaseModel):
    name:      str = Field(..., description="Tool name to call")
    arguments: dict[str, Any] = Field(default_factory=dict, description="Tool input parameters")


# ---------------------------------------------------------------------------
# SSE helpers (T-29)
# ---------------------------------------------------------------------------

def _sse_event(event: str, data: Any) -> str:
    """Format a single SSE event frame."""
    payload = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {payload}\n\n"


async def _stream_tool_execution(
    tool_name: str,
    params:    dict[str, Any],
    key_ctx:   _McpKeyContext,
    progress_interval_s: float = 2.0,
) -> AsyncGenerator[str, None]:
    """Execute tool and yield SSE events, writing McpCallLog on completion."""
    yield _sse_event("progress", {
        "stage":   "started",
        "tool":    tool_name,
        "message": f"Đang thực thi {tool_name}…",
    })

    queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()

    async def _run_tool() -> None:
        try:
            result, elapsed_ms = await execute_tool(tool_name, params)
            validated = _validate_tool_output(tool_name, result)
            await queue.put({"ok": True, "result": validated, "elapsed_ms": elapsed_ms})
        except Exception as exc:
            await queue.put({"ok": False, "error": str(exc), "elapsed_ms": 0})

    task = asyncio.create_task(_run_tool())

    elapsed = 0.0
    final_item: dict[str, Any] | None = None

    while not task.done():
        try:
            item = await asyncio.wait_for(queue.get(), timeout=progress_interval_s)
            final_item = item
            break
        except asyncio.TimeoutError:
            elapsed += progress_interval_s
            yield _sse_event("progress", {
                "stage":   "running",
                "tool":    tool_name,
                "elapsed": elapsed,
                "message": f"{tool_name} đang xử lý ({elapsed:.0f}s)…",
            })
        except Exception as exc:
            yield _sse_event("error", {
                "content": [{"type": "text", "text": f"Stream error: {exc}"}],
                "isError": True,
            })
            return

    # Drain queue if task completed before timeout
    if final_item is None:
        try:
            final_item = queue.get_nowait()
        except asyncio.QueueEmpty:
            yield _sse_event("error", {
                "content": [{"type": "text", "text": "Tool completed but returned no result"}],
                "isError": True,
            })
            return

    if final_item["ok"]:
        result = final_item["result"]
        elapsed_ms = final_item["elapsed_ms"]
        is_incomplete = result.get("output_incomplete", False)

        yield _sse_event("result", {
            "content":    [{"type": "text", "text": json.dumps(result, ensure_ascii=False)}],
            "isError":    bool("error" in result),
            "elapsed_ms": elapsed_ms,
        })

        # T-36: Audit log — fire and forget
        asyncio.create_task(_log_mcp_call(
            key_ctx=key_ctx,
            tool_name=tool_name,
            inputs=params,
            outputs=result,
            is_error=bool("error" in result),
            is_streaming=True,
            execution_ms=elapsed_ms,
            output_incomplete=is_incomplete,
            missing_fields=result.get("missing_fields"),
        ))
    else:
        yield _sse_event("error", {
            "content": [{"type": "text", "text": f"Tool error: {final_item['error']}"}],
            "isError": True,
        })

        asyncio.create_task(_log_mcp_call(
            key_ctx=key_ctx,
            tool_name=tool_name,
            inputs=params,
            outputs={"error": final_item["error"]},
            is_error=True,
            is_streaming=True,
            execution_ms=final_item.get("elapsed_ms", 0),
        ))


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/manifest", dependencies=[Depends(_require_mcp_key)])
async def mcp_manifest() -> dict[str, Any]:
    """MCP server manifest — describes server capabilities."""
    return {
        "protocolVersion": "2025-03-26",
        "serverInfo": {
            "name":    "hdtv-ai-mcp-server",
            "version": "1.2.0",  # bumped for T-36
        },
        "capabilities": {
            "tools":     {"listChanged": False},
            "streaming": {"supported": True},
            "audit":     {"supported": True},   # T-36: audit trail available
        },
        "instructions": (
            "HDTV AI Platform MCP Server. "
            "Provides tools for EVN Hanoi appraisal: ERP budget/inventory checks, "
            "DOffice lookup, PMIS project status, Legal GraphRAG, and OCR extraction. "
            "Pass X-MCP-API-Key header with all requests. "
            "Use POST /mcp/tools/call/stream for long-running tools. "
            "Manage API keys at GET /api/v1/api-keys."
        ),
    }


@router.post("/tools/list", dependencies=[Depends(_require_mcp_key)])
async def mcp_list_tools() -> dict[str, Any]:
    """List all available tools with their JSON Schema definitions."""
    dynamic_tools = await list_tools_dynamic()

    tools_out: list[dict[str, Any]] = []
    for t in dynamic_tools:
        schema = _TOOL_INPUT_SCHEMAS.get(t["name"], {
            "type": "object",
            "properties": {
                "dossier_id": {"type": "integer"},
                "query":      {"type": "string"},
            },
        })
        tools_out.append({
            "name":        t["name"],
            "description": t["description"],
            "inputSchema": schema,
        })

    return {"tools": tools_out}


@router.post("/tools/call")
async def mcp_call_tool(
    body: McpToolCallRequest,
    key_ctx: _McpKeyContext = Depends(_require_mcp_key),
) -> dict[str, Any]:
    """Execute a named tool with provided arguments (synchronous).

    T-29: validates output against _TOOL_OUTPUT_SCHEMAS before returning.
    T-36: writes McpCallLog row after execution.
    """
    tool_name = body.name
    params    = body.arguments

    dynamic_tools = await list_tools_dynamic()
    known_names = {t["name"] for t in dynamic_tools}
    if tool_name not in known_names:
        asyncio.create_task(_log_mcp_call(
            key_ctx=key_ctx, tool_name=tool_name, inputs=params,
            outputs={"error": f"Unknown tool: {tool_name}"},
            is_error=True, is_streaming=False, execution_ms=0,
        ))
        return {
            "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
            "isError": True,
        }

    start = time.perf_counter()
    try:
        result, elapsed_ms = await execute_tool(tool_name, params)
        result = _validate_tool_output(tool_name, result)

        is_error = bool("error" in result)
        is_incomplete = result.get("output_incomplete", False)
        result_text = json.dumps(result, ensure_ascii=False, indent=2)

        TOOL_CALLS.labels(tool_name=tool_name, status="ok" if not is_error else "error").inc()
        TOOL_DURATION.labels(tool_name=tool_name).observe(time.perf_counter() - start)

        # T-36: Audit log — fire and forget
        asyncio.create_task(_log_mcp_call(
            key_ctx=key_ctx,
            tool_name=tool_name,
            inputs=params,
            outputs=result,
            is_error=is_error,
            is_streaming=False,
            execution_ms=elapsed_ms,
            output_incomplete=is_incomplete,
            missing_fields=result.get("missing_fields"),
        ))

        logger.info("MCP tool_call %s → %dms isError=%s prefix=%s",
                    tool_name, elapsed_ms, is_error, key_ctx.key_prefix)

        return {
            "content": [{"type": "text", "text": result_text}],
            "isError": is_error or is_incomplete,
            "_meta":   {"execution_ms": elapsed_ms},
        }

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        TOOL_CALLS.labels(tool_name=tool_name, status="exception").inc()
        logger.exception("MCP tool_call %s raised exception", tool_name)

        asyncio.create_task(_log_mcp_call(
            key_ctx=key_ctx,
            tool_name=tool_name,
            inputs=params,
            outputs={"error": str(exc)},
            is_error=True,
            is_streaming=False,
            execution_ms=elapsed_ms,
        ))
        return {
            "content": [{"type": "text", "text": f"Tool execution error: {exc}"}],
            "isError": True,
        }


@router.post("/tools/call/stream")
async def mcp_call_tool_stream(
    body: McpToolCallRequest,
    key_ctx: _McpKeyContext = Depends(_require_mcp_key),
) -> StreamingResponse:
    """T-29: SSE streaming endpoint. T-36: writes McpCallLog after stream ends."""
    tool_name = body.name
    params    = body.arguments

    dynamic_tools = await list_tools_dynamic()
    known_names = {t["name"] for t in dynamic_tools}
    if tool_name not in known_names:
        async def _error_stream() -> AsyncGenerator[str, None]:
            yield _sse_event("error", {
                "content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}],
                "isError": True,
            })
        return StreamingResponse(
            _error_stream(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    return StreamingResponse(
        _stream_tool_execution(tool_name, params, key_ctx),
        media_type="text/event-stream",
        headers={
            "Cache-Control":     "no-cache",
            "X-Accel-Buffering": "no",
            "Connection":        "keep-alive",
        },
    )


@router.get("/audit-logs")
async def mcp_audit_logs(
    limit: int = Query(default=50, ge=1, le=500, description="Max rows to return"),
    tool_name: str | None = Query(default=None, description="Filter by tool name"),
    key_ctx: _McpKeyContext = Depends(_require_mcp_key),
) -> list[dict[str, Any]]:
    """T-36: List recent MCP call audit logs.

    Returns last `limit` McpCallLog rows, newest first.
    Optionally filtered by tool_name.
    """
    try:
        from app.core.database import async_session_factory
        from app.models.entities import McpCallLog
        from sqlalchemy import select

        async with async_session_factory() as db:
            stmt = select(McpCallLog).order_by(McpCallLog.created_at.desc()).limit(limit)
            if tool_name:
                stmt = stmt.where(McpCallLog.tool_name == tool_name)

            rows = (await db.execute(stmt)).scalars().all()
            return [
                {
                    "id":               row.id,
                    "api_key_prefix":   row.api_key_prefix,
                    "tool_name":        row.tool_name,
                    "is_error":         row.is_error,
                    "is_streaming":     row.is_streaming,
                    "execution_ms":     row.execution_ms,
                    "output_incomplete": row.output_incomplete,
                    "missing_fields":   row.missing_fields,
                    "created_at":       row.created_at.isoformat(),
                }
                for row in rows
            ]
    except Exception as exc:
        logger.error("MCP audit-logs query failed: %s", exc)
        return []


@router.get("/health")
async def mcp_health() -> dict[str, str]:
    """MCP server health — no auth required."""
    return {
        "status":    "ok",
        "server":    "hdtv-ai-mcp-server",
        "streaming": "supported",
        "audit":     "enabled",  # T-36
    }
