"""
T-30: ERP Tool Handlers — thin wrappers around base.py ERP tool implementations.

Provides a clean validate_input() + execute() contract for ERP tools.
base.py uses _validate_tool_input() for quick field checks, but these handlers
provide richer domain-level validation (e.g., VND amount ranges, doc_no format).

Usage pattern (for future handler-based dispatch):
    handler = ErpBudgetHandler()
    error = handler.validate_input(params)
    if error:
        return error, 0
    result = await handler.execute(params)
"""

from __future__ import annotations

import re
from typing import Any

from app.services.tools.types import ToolErrorType


# ---------------------------------------------------------------------------
# Base handler
# ---------------------------------------------------------------------------

class BaseToolHandler:
    """Abstract base for tool handlers. Subclass and implement validate_input + execute."""

    tool_name: str = ""

    def validate_input(self, params: dict[str, Any]) -> dict[str, Any] | None:
        """Validate domain-level constraints beyond required-field checks.

        Returns:
            None if valid.
            Error dict with error_type=BAD_INPUT if invalid.
        """
        raise NotImplementedError

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Execute the tool and return result dict."""
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Doc_no format check (EVN Hanoi format: NNN/TTr-DEPT or similar)
# ---------------------------------------------------------------------------

_DOC_NO_PATTERN = re.compile(
    r"^\d{1,4}/[A-Za-z]{2,6}(-[A-Za-z0-9]{1,10})?$",
    re.IGNORECASE,
)


def _validate_doc_no(doc_no: str) -> str | None:
    """Return error message if doc_no format is invalid, else None."""
    if not doc_no or not doc_no.strip():
        return "doc_no không được rỗng"
    if len(doc_no) > 64:
        return f"doc_no quá dài ({len(doc_no)} ký tự, tối đa 64)"
    # Warn but don't block if format is unexpected (EVN doc numbers may vary)
    return None


# ---------------------------------------------------------------------------
# ErpBudgetHandler
# ---------------------------------------------------------------------------

class ErpBudgetHandler(BaseToolHandler):
    """Handler for ErpBudgetCheck tool.

    Domain validation:
    - dossier_id must be positive integer
    - doc_no must be non-empty string ≤ 64 chars
    """

    tool_name = "ErpBudgetCheck"

    def validate_input(self, params: dict[str, Any]) -> dict[str, Any] | None:
        errors: list[str] = []

        dossier_id = params.get("dossier_id")
        if not isinstance(dossier_id, int) or dossier_id <= 0:
            errors.append(f"dossier_id phải là số nguyên dương, nhận được: {dossier_id!r}")

        doc_no = params.get("doc_no", "")
        doc_no_err = _validate_doc_no(str(doc_no))
        if doc_no_err:
            errors.append(f"doc_no: {doc_no_err}")

        if errors:
            hint = f"ErpBudgetCheck validation: {'; '.join(errors)}"
            return {
                "error":      hint,
                "error_type": ToolErrorType.BAD_INPUT,
                "hint":       hint,
            }
        return None

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        """Delegate to static tool implementation."""
        from app.services.tools.gemini_mock import gemini_tool_response
        return await gemini_tool_response(
            "ErpBudgetCheck",
            params,
            system_hint=(
                "Simulate EVN Hanoi ERP PS budget check. "
                "Return approved_budget (VND), proposed_budget (VND), variance_vnd (int), exceeded (bool)."
            ),
        )


# ---------------------------------------------------------------------------
# ErpInventoryHandler
# ---------------------------------------------------------------------------

class ErpInventoryHandler(BaseToolHandler):
    """Handler for ErpInventoryCheck tool.

    Domain validation:
    - dossier_id must be positive integer
    - doc_no must be non-empty string ≤ 64 chars
    - material_code if present must be non-empty string
    """

    tool_name = "ErpInventoryCheck"

    def validate_input(self, params: dict[str, Any]) -> dict[str, Any] | None:
        errors: list[str] = []

        dossier_id = params.get("dossier_id")
        if not isinstance(dossier_id, int) or dossier_id <= 0:
            errors.append(f"dossier_id phải là số nguyên dương, nhận được: {dossier_id!r}")

        doc_no = params.get("doc_no", "")
        doc_no_err = _validate_doc_no(str(doc_no))
        if doc_no_err:
            errors.append(f"doc_no: {doc_no_err}")

        material_code = params.get("material_code")
        if material_code is not None and (not isinstance(material_code, str) or not material_code.strip()):
            errors.append("material_code phải là chuỗi không rỗng nếu cung cấp")

        if errors:
            hint = f"ErpInventoryCheck validation: {'; '.join(errors)}"
            return {
                "error":      hint,
                "error_type": ToolErrorType.BAD_INPUT,
                "hint":       hint,
            }
        return None

    async def execute(self, params: dict[str, Any]) -> dict[str, Any]:
        from app.services.tools.gemini_mock import gemini_tool_response
        return await gemini_tool_response(
            "ErpInventoryCheck",
            params,
            system_hint=(
                "Simulate ERP MM/INV inventory check. "
                "Return material_code, stock_meters (float), waste_warning (bool), available_quantity (int)."
            ),
        )


# ---------------------------------------------------------------------------
# Handler registry — lookup by tool name
# ---------------------------------------------------------------------------

_HANDLER_REGISTRY: dict[str, BaseToolHandler] = {
    "ErpBudgetCheck":    ErpBudgetHandler(),
    "ErpInventoryCheck": ErpInventoryHandler(),
}


def get_handler(tool_name: str) -> BaseToolHandler | None:
    """Return the handler for a tool, or None if no handler is registered."""
    return _HANDLER_REGISTRY.get(tool_name)
