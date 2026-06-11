"""Shared types for plan-execute-reflect orchestrator (T-17)."""

from typing import Any, Literal, TypedDict


class PlanStep(TypedDict, total=False):
    id: str
    tool: str
    parallel_group: str | None
    depends_on: list[str]
    tool_input: dict[str, Any]


class ExecutionPlan(TypedDict, total=False):
    goal: str
    max_revisions: int
    steps: list[PlanStep]
    _fallback: bool


ReflectionVerdict = Literal["sufficient", "revise", "escalate"]


class ReflectionResult(TypedDict, total=False):
    verdict: ReflectionVerdict
    reason: str
    revised_steps: list[PlanStep]


class CriticResult(TypedDict, total=False):
    approved: bool
    issues: list[str]
    suggested_fixes: list[str]
    source: str
