"""Tool execution types — kept separate from base.py to avoid circular imports with handlers."""

from __future__ import annotations

from enum import Enum


class ToolErrorType(str, Enum):
    """Classifies tool errors so the agent loop can decide: retry vs fix-input vs escalate."""
    TRANSIENT   = "transient"
    BAD_INPUT   = "bad_input"
    UNAVAILABLE = "unavailable"
    UNKNOWN     = "unknown"
