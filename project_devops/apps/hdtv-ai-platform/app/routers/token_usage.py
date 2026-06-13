"""Token Usage router — aggregate LLM token consumption for the dashboard screen.

Endpoints:
  GET /token-usage/summary        — totals + by-backend breakdown + cost estimate
  GET /token-usage/daily          — daily time series (last N days)
  GET /token-usage/by-role        — breakdown per AgentRole
  GET /token-usage/by-dossier     — top N dossiers by token spend
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import LlmTokenUsage

router = APIRouter()

# ---------------------------------------------------------------------------
# Cost estimation constants (USD per 1M tokens, as of 2026)
# ---------------------------------------------------------------------------
_COST_PER_M: dict[str, dict[str, float]] = {
    "gemini": {"prompt": 0.15, "completion": 0.60},
    "local":  {"prompt": 0.0,  "completion": 0.0},   # electricity only
}

def _estimate_cost_usd(backend: str, prompt_tokens: int, completion_tokens: int) -> float:
    rates = _COST_PER_M.get(backend, _COST_PER_M["gemini"])
    return (
        prompt_tokens     / 1_000_000 * rates["prompt"] +
        completion_tokens / 1_000_000 * rates["completion"]
    )


# ---------------------------------------------------------------------------
# GET /token-usage/summary
# ---------------------------------------------------------------------------

@router.get("/summary")
async def get_token_usage_summary(
    days: int = Query(30, ge=1, le=365, description="Look-back window in days"),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Overall token usage summary with cost estimate."""
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)

    # Aggregate totals grouped by backend
    rows = (
        await db.execute(
            select(
                LlmTokenUsage.backend,
                func.sum(LlmTokenUsage.prompt_tokens).label("prompt"),
                func.sum(LlmTokenUsage.completion_tokens).label("completion"),
                func.sum(LlmTokenUsage.total_tokens).label("total"),
                func.count(LlmTokenUsage.id).label("calls"),
            )
            .where(LlmTokenUsage.created_at >= since)
            .group_by(LlmTokenUsage.backend)
        )
    ).all()

    by_backend: list[dict[str, Any]] = []
    grand_total = grand_prompt = grand_completion = grand_calls = 0
    grand_cost = 0.0

    for r in rows:
        cost = _estimate_cost_usd(r.backend, r.prompt or 0, r.completion or 0)
        grand_cost += cost
        grand_total += r.total or 0
        grand_prompt += r.prompt or 0
        grand_completion += r.completion or 0
        grand_calls += r.calls or 0
        by_backend.append({
            "backend":           r.backend,
            "prompt_tokens":     r.prompt or 0,
            "completion_tokens": r.completion or 0,
            "total_tokens":      r.total or 0,
            "calls":             r.calls or 0,
            "cost_usd":          round(cost, 6),
        })

    return {
        "period_days":       days,
        "since":             since.isoformat(),
        "total_calls":       grand_calls,
        "prompt_tokens":     grand_prompt,
        "completion_tokens": grand_completion,
        "total_tokens":      grand_total,
        "cost_usd":          round(grand_cost, 6),
        "by_backend":        by_backend,
    }


# ---------------------------------------------------------------------------
# GET /token-usage/daily
# ---------------------------------------------------------------------------

@router.get("/daily")
async def get_token_usage_daily(
    days: int = Query(30, ge=1, le=180),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Daily token usage time series — one row per (date, backend)."""
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)

    rows = (
        await db.execute(
            select(
                func.date_trunc("day", LlmTokenUsage.created_at).label("day"),
                LlmTokenUsage.backend,
                func.sum(LlmTokenUsage.prompt_tokens).label("prompt"),
                func.sum(LlmTokenUsage.completion_tokens).label("completion"),
                func.sum(LlmTokenUsage.total_tokens).label("total"),
                func.count(LlmTokenUsage.id).label("calls"),
            )
            .where(LlmTokenUsage.created_at >= since)
            .group_by(text("1"), LlmTokenUsage.backend)
            .order_by(text("1"), LlmTokenUsage.backend)
        )
    ).all()

    return [
        {
            "date":              r.day.strftime("%Y-%m-%d") if r.day else None,
            "backend":           r.backend,
            "prompt_tokens":     r.prompt or 0,
            "completion_tokens": r.completion or 0,
            "total_tokens":      r.total or 0,
            "calls":             r.calls or 0,
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# GET /token-usage/by-role
# ---------------------------------------------------------------------------

@router.get("/by-role")
async def get_token_usage_by_role(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Token usage per AgentRole — useful for tuning which roles are expensive."""
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)

    rows = (
        await db.execute(
            select(
                LlmTokenUsage.role,
                LlmTokenUsage.backend,
                func.sum(LlmTokenUsage.prompt_tokens).label("prompt"),
                func.sum(LlmTokenUsage.completion_tokens).label("completion"),
                func.sum(LlmTokenUsage.total_tokens).label("total"),
                func.count(LlmTokenUsage.id).label("calls"),
                func.avg(LlmTokenUsage.total_tokens).label("avg_tokens"),
                func.avg(LlmTokenUsage.duration_ms).label("avg_ms"),
            )
            .where(LlmTokenUsage.created_at >= since)
            .group_by(LlmTokenUsage.role, LlmTokenUsage.backend)
            .order_by(func.sum(LlmTokenUsage.total_tokens).desc())
        )
    ).all()

    return [
        {
            "role":              r.role,
            "backend":           r.backend,
            "prompt_tokens":     r.prompt or 0,
            "completion_tokens": r.completion or 0,
            "total_tokens":      r.total or 0,
            "calls":             r.calls or 0,
            "avg_tokens_per_call": round(r.avg_tokens or 0),
            "avg_duration_ms":   round(r.avg_ms or 0),
            "cost_usd":          round(_estimate_cost_usd(r.backend, r.prompt or 0, r.completion or 0), 6),
        }
        for r in rows
    ]


# ---------------------------------------------------------------------------
# GET /token-usage/by-dossier
# ---------------------------------------------------------------------------

@router.get("/by-dossier")
async def get_token_usage_by_dossier(
    days: int = Query(30, ge=1, le=365),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    """Top N dossiers by total token spend — for cost attribution."""
    since = datetime.now(tz=timezone.utc) - timedelta(days=days)

    rows = (
        await db.execute(
            select(
                LlmTokenUsage.dossier_id,
                func.sum(LlmTokenUsage.prompt_tokens).label("prompt"),
                func.sum(LlmTokenUsage.completion_tokens).label("completion"),
                func.sum(LlmTokenUsage.total_tokens).label("total"),
                func.count(LlmTokenUsage.id).label("calls"),
            )
            .where(
                LlmTokenUsage.created_at >= since,
                LlmTokenUsage.dossier_id.isnot(None),
            )
            .group_by(LlmTokenUsage.dossier_id)
            .order_by(func.sum(LlmTokenUsage.total_tokens).desc())
            .limit(limit)
        )
    ).all()

    return [
        {
            "dossier_id":        r.dossier_id,
            "prompt_tokens":     r.prompt or 0,
            "completion_tokens": r.completion or 0,
            "total_tokens":      r.total or 0,
            "calls":             r.calls or 0,
        }
        for r in rows
    ]
