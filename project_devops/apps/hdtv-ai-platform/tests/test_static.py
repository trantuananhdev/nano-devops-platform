"""T-45: Offline static integration tests — no server required.

Run from repo root:
    python -m pytest project_devops/apps/hdtv-ai-platform/tests/test_static.py -q
"""
from __future__ import annotations

import inspect
from typing import get_type_hints

import pytest
from fastapi import FastAPI

from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpen, CircuitState
from app.services.tools.base import _validate_tool_input
from app.services.tools.types import ToolErrorType


# ---------------------------------------------------------------------------
# Import smoke tests — modules must load without live infrastructure
# ---------------------------------------------------------------------------

def test_import_main_create_app() -> None:
    # Import create_app only — avoid module-level `app = create_app()` side effects
    import importlib

    main_mod = importlib.import_module("app.main")
    app = main_mod.create_app()
    assert isinstance(app, FastAPI)
    assert app.title


def test_import_orchestrator_planner() -> None:
    from app.services.orchestrator import planner

    assert callable(planner.create_plan)
    assert callable(planner.validate_plan)
    assert callable(planner.build_fallback_plan)


def test_import_orchestrator_executor() -> None:
    from app.services.orchestrator import executor

    assert callable(executor.execute_plan_steps)


def test_import_orchestrator_reflector() -> None:
    from app.services.orchestrator import reflector

    assert callable(reflector.reflect_on_results)


def test_import_orchestrator_critic() -> None:
    from app.services.orchestrator import critic

    assert callable(critic.review_draft)


def test_import_circuit_breaker_module() -> None:
    from app.core import circuit_breaker as cb

    assert cb.CircuitState.CLOSED.value == "closed"
    assert cb.CircuitState.OPEN.value == "open"
    assert cb.CircuitState.HALF_OPEN.value == "half_open"


def test_memory_retriever_signatures() -> None:
    from app.services.memory import retriever

    sig = inspect.signature(retriever.retrieve_relevant_memories)
    params = list(sig.parameters)
    assert "session" in params
    assert "dossier_id" in params
    assert "query" in params

    cross_sig = inspect.signature(retriever.retrieve_cross_dossier_memories)
    assert "unit" in cross_sig.parameters

    pref_sig = inspect.signature(retriever.build_preference_context)
    hints = get_type_hints(retriever.build_preference_context)
    assert "preferences" in hints or "preferences" in pref_sig.parameters


# ---------------------------------------------------------------------------
# Tool harness unit tests
# ---------------------------------------------------------------------------

def test_tool_error_type_enum_values() -> None:
    values = {e.value for e in ToolErrorType}
    assert values >= {"transient", "bad_input", "unavailable", "unknown"}


def test_validate_tool_input_known_good() -> None:
    result = _validate_tool_input(
        "ErpBudgetCheck",
        {"dossier_id": 1, "doc_no": "TT-HDTV-001"},
    )
    assert result is None


def test_validate_tool_input_missing_fields() -> None:
    result = _validate_tool_input("LegalGraphRAG", {})
    assert result is not None
    assert result["error_type"] == ToolErrorType.BAD_INPUT
    assert "query" in result.get("missing_fields", [])


def test_validate_tool_input_wrong_type() -> None:
    result = _validate_tool_input(
        "ErpBudgetCheck",
        {"dossier_id": "not-int", "doc_no": "TT-001"},
    )
    assert result is not None
    assert result["error_type"] == ToolErrorType.BAD_INPUT
    assert "type_errors" in result


# ---------------------------------------------------------------------------
# Circuit breaker behaviour (async, in-memory)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_circuit_breaker_closed_allows_calls() -> None:
    cb = CircuitBreaker("test-local", failure_threshold=3, cooldown_s=1)

    async def ok() -> str:
        return "ok"

    assert await cb.call(ok) == "ok"
    assert cb.state == CircuitState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures() -> None:
    cb = CircuitBreaker("test-trip", failure_threshold=2, window_s=60, cooldown_s=30)

    async def fail() -> None:
        raise RuntimeError("simulated LLM error")

    for _ in range(2):
        with pytest.raises(RuntimeError):
            await cb.call(fail)

    assert cb.state == CircuitState.OPEN

    with pytest.raises(CircuitBreakerOpen):
        await cb.call(fail)
