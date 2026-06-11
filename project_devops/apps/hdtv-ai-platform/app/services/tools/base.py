"""
Tool Execution Base — T-30: Execution Harness with input validation, per-tool timeout,
error taxonomy, and retry support.

Public API:
  execute_tool(name, params)         — main dispatcher: validate → timeout-guarded call → metrics
  ToolErrorType                      — enum for error taxonomy (TRANSIENT | BAD_INPUT | UNAVAILABLE | UNKNOWN)
  STATIC_TOOL_IMPLS                  — registry of tool name → async function
  list_tools() / list_tools_dynamic() — tool discovery

Error taxonomy (attached as error_type in every error response):
  TRANSIENT     — network/timeout; safe to retry with same input
  BAD_INPUT     — missing/invalid required field; do NOT retry, fix input first
  UNAVAILABLE   — tool function not found; fallback or skip
  UNKNOWN       — unexpected exception; retry once then escalate
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Awaitable, Callable

from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import async_session_factory
from app.core.metrics import TOOL_CALLS, TOOL_DURATION, TOOL_INPUT_VALIDATION_ERRORS, TOOL_TIMEOUTS
from app.models.entities import ToolConfig
from app.services.tools.gemini_mock import gemini_tool_response
from app.services.tools.legal_rag import legal_graph_rag
from app.services.tools.sandbox_executor import sandbox_shell_tool
from app.services.tools.types import ToolErrorType
from app.tools.handlers.erp_handler import get_handler

logger = logging.getLogger(__name__)

ToolFn = Callable[[dict[str, Any]], Awaitable[dict[str, Any]]]


# ---------------------------------------------------------------------------
# T-30: Required input fields per tool (for pre-call validation)
# ---------------------------------------------------------------------------

_TOOL_INPUT_REQUIRED_FIELDS: dict[str, list[str]] = {
    "ErpBudgetCheck":    ["dossier_id", "doc_no"],
    "ErpInventoryCheck": ["dossier_id", "doc_no"],
    "DOfficeLookup":     ["dossier_id", "doc_no"],
    "PmisProjectCheck":  ["dossier_id", "doc_no"],
    "LegalGraphRAG":     ["query"],
    "EcoOcrExtract":     ["dossier_id"],
    "SandboxShell":      ["command"],
}

# Field type expectations — basic sanity check (not JSON Schema level)
_TOOL_INPUT_FIELD_TYPES: dict[str, type] = {
    "dossier_id": int,
    "doc_no":     str,
    "query":      str,
    "command":    str,
}


def _validate_tool_input(name: str, params: dict[str, Any]) -> dict[str, Any] | None:
    """Validate required input fields for a tool.

    Args:
        name:   Tool name
        params: Input parameters dict

    Returns:
        None if valid.
        Error dict with error_type="bad_input" and actionable hint if invalid.
    """
    required = _TOOL_INPUT_REQUIRED_FIELDS.get(name)
    if not required:
        return None  # No schema defined → pass through

    missing = [f for f in required if f not in params]
    if missing:
        hint = (
            f"Tool '{name}' thiếu field bắt buộc: {', '.join(missing)}. "
            f"Cần cung cấp: {', '.join(required)}"
        )
        TOOL_INPUT_VALIDATION_ERRORS.labels(tool_name=name).inc()
        logger.warning("Tool %s: input validation failed — missing fields %s", name, missing)
        return {
            "error":        hint,
            "error_type":   ToolErrorType.BAD_INPUT,
            "missing_fields": missing,
            "hint":         hint,
        }

    # Type check on present fields
    type_errors: list[str] = []
    for field, expected_type in _TOOL_INPUT_FIELD_TYPES.items():
        if field in params and not isinstance(params[field], expected_type):
            type_errors.append(
                f"'{field}' phải là {expected_type.__name__}, nhận được {type(params[field]).__name__}"
            )

    if type_errors:
        hint = f"Tool '{name}' type error: {'; '.join(type_errors)}"
        TOOL_INPUT_VALIDATION_ERRORS.labels(tool_name=name).inc()
        logger.warning("Tool %s: input type validation failed — %s", name, type_errors)
        return {
            "error":      hint,
            "error_type": ToolErrorType.BAD_INPUT,
            "type_errors": type_errors,
            "hint":        hint,
        }

    return None


# ---------------------------------------------------------------------------
# Static tool implementations
# ---------------------------------------------------------------------------

async def _erp_budget_check(params: dict[str, Any]) -> dict[str, Any]:
    return await gemini_tool_response(
        "ErpBudgetCheck",
        params,
        system_hint="Simulate EVN Hanoi ERP PS budget check. Return approved_budget, proposed_budget, variance_vnd, exceeded (bool).",
    )


async def _erp_inventory_check(params: dict[str, Any]) -> dict[str, Any]:
    return await gemini_tool_response(
        "ErpInventoryCheck",
        params,
        system_hint="Simulate ERP MM/INV inventory. Return material_code, stock_meters, waste_warning (bool).",
    )


async def _doffice_lookup(params: dict[str, Any]) -> dict[str, Any]:
    return await gemini_tool_response(
        "DOfficeLookup",
        params,
        system_hint="Simulate DOffice document registry lookup. Return doc_status, signed, attachments.",
    )


async def _pmis_project_check(params: dict[str, Any]) -> dict[str, Any]:
    return await gemini_tool_response(
        "PmisProjectCheck",
        params,
        system_hint="Simulate PMIS project status. Return project_code, phase, on_schedule (bool).",
    )


async def _eco_ocr_extract(params: dict[str, Any]) -> dict[str, Any]:
    return await gemini_tool_response(
        "EcoOcrExtract",
        params,
        system_hint="Simulate EcoOCR text extraction from PDF. Return extracted_text summary.",
    )


# Registry: tool name → implementation
STATIC_TOOL_IMPLS: dict[str, ToolFn] = {
    "ErpBudgetCheck":    _erp_budget_check,
    "ErpInventoryCheck": _erp_inventory_check,
    "DOfficeLookup":     _doffice_lookup,
    "PmisProjectCheck":  _pmis_project_check,
    "LegalGraphRAG":     legal_graph_rag,
    "EcoOcrExtract":     _eco_ocr_extract,
    "SandboxShell":      sandbox_shell_tool,
}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

async def get_active_tools() -> list[ToolConfig]:
    async with async_session_factory() as session:
        result = await session.execute(
            select(ToolConfig)
            .where(ToolConfig.is_active.is_(True))
            .order_by(ToolConfig.priority.desc(), ToolConfig.name)
        )
        return list(result.scalars().all())


async def get_tool_by_name(name: str) -> ToolConfig | None:
    async with async_session_factory() as session:
        result = await session.execute(
            select(ToolConfig).where(ToolConfig.name == name)
        )
        return result.scalar_one_or_none()


def list_tools() -> list[str]:
    return list(STATIC_TOOL_IMPLS.keys())


async def list_tools_dynamic() -> list[dict[str, Any]]:
    tools = await get_active_tools()
    return [
        {
            "name":        t.name,
            "description": t.description,
            "category":    t.category,
            "priority":    t.priority,
            "is_active":   t.is_active,
        }
        for t in tools
    ]


# ---------------------------------------------------------------------------
# T-30: Main dispatcher — validate → timeout-guarded call → classify error
# ---------------------------------------------------------------------------

async def execute_tool(name: str, params: dict[str, Any]) -> tuple[dict[str, Any], int]:
    """Execute a tool with input validation, per-tool timeout, and error taxonomy.

    Flow:
      1. Validate required input fields → reject immediately with BAD_INPUT (no LLM call)
      2. Look up implementation (static registry or DB fallback)
      3. Call with asyncio.wait_for(tool_execution_timeout_s) → TRANSIENT on timeout
      4. Classify any exception into ToolErrorType
      5. Emit Prometheus metrics + error_type on every path

    Args:
        name:   Tool name (must match STATIC_TOOL_IMPLS or DB ToolConfig)
        params: Input parameters (validated against _TOOL_INPUT_REQUIRED_FIELDS)

    Returns:
        (result_dict, elapsed_ms) — result_dict always has error_type on error path
    """
    cfg = get_settings()
    start = time.perf_counter()

    # ── Step 1: Input validation ──────────────────────────────────────────
    # First: schema-level required-field check (fast, no DB)
    validation_error = _validate_tool_input(name, params)
    if validation_error:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        TOOL_CALLS.labels(tool_name=name, status="error").inc()
        return validation_error, elapsed_ms

    # Second: domain-level handler validation (richer checks, e.g. doc_no format)
    handler = get_handler(name)
    if handler is not None:
        handler_error = handler.validate_input(params)
        if handler_error:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            TOOL_INPUT_VALIDATION_ERRORS.labels(tool_name=name).inc()
            TOOL_CALLS.labels(tool_name=name, status="error").inc()
            return handler_error, elapsed_ms

    # ── Step 2: Resolve implementation ───────────────────────────────────
    tool_config = await get_tool_by_name(name)
    fn = STATIC_TOOL_IMPLS.get(name)

    if not fn and tool_config and tool_config.fallback_response:
        # DB-only tool with static fallback response
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        TOOL_CALLS.labels(tool_name=name, status="ok").inc()
        TOOL_DURATION.labels(tool_name=name).observe(elapsed_ms / 1000.0)
        return tool_config.fallback_response, elapsed_ms

    if not fn:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        TOOL_CALLS.labels(tool_name=name, status="error").inc()
        return {
            "error":        f"Unknown tool: {name}",
            "error_type":   ToolErrorType.UNAVAILABLE,
            "hint":         f"Tool '{name}' không tồn tại trong registry. Kiểm tra tên tool.",
        }, elapsed_ms

    # ── Step 3: Timeout-guarded execution ────────────────────────────────
    timeout_s = float(cfg.tool_execution_timeout_s)
    try:
        result: dict[str, Any] = await asyncio.wait_for(
            fn(params),
            timeout=timeout_s,
        )
    except asyncio.TimeoutError:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        TOOL_CALLS.labels(tool_name=name, status="error").inc()
        TOOL_DURATION.labels(tool_name=name).observe(elapsed_ms / 1000.0)
        TOOL_TIMEOUTS.labels(tool_name=name).inc()
        logger.warning("Tool %s timed out after %.0fs", name, timeout_s)
        return {
            "error":      f"Tool '{name}' timeout sau {timeout_s:.0f}s",
            "error_type": ToolErrorType.TRANSIENT,
            "hint":       "Timeout do Gemini API chậm hoặc network. Retry an toàn.",
        }, elapsed_ms

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        # Use DB fallback if available
        if tool_config and tool_config.fallback_response:
            logger.warning("Tool %s raised %s — using DB fallback", name, exc)
            TOOL_CALLS.labels(tool_name=name, status="ok").inc()
            TOOL_DURATION.labels(tool_name=name).observe(elapsed_ms / 1000.0)
            return tool_config.fallback_response, elapsed_ms

        TOOL_CALLS.labels(tool_name=name, status="error").inc()
        TOOL_DURATION.labels(tool_name=name).observe(elapsed_ms / 1000.0)
        logger.exception("Tool %s raised unexpected exception", name)
        return {
            "error":      str(exc),
            "error_type": ToolErrorType.UNKNOWN,
            "hint":       f"Lỗi không xác định từ '{name}'. Thử retry 1 lần, sau đó escalate.",
        }, elapsed_ms

    # ── Step 4: Success metrics ───────────────────────────────────────────
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    status = "error" if "error" in result else "ok"
    if status == "error" and "error_type" not in result:
        result["error_type"] = ToolErrorType.UNKNOWN
    TOOL_CALLS.labels(tool_name=name, status=status).inc()
    TOOL_DURATION.labels(tool_name=name).observe(elapsed_ms / 1000.0)
    return result, elapsed_ms
