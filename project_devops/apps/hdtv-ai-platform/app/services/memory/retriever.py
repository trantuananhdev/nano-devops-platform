"""T-15 / T-16: Memory Retriever — retrieve_relevant_memories() + cross-dossier support.

Strategy:
1. Try Chroma vector query (top_k chunks) with dossier-scoped WHERE filter.
2. Degraded fallback: if Chroma unreachable or empty, load all PG rows for dossier.

T-16 additions:
- retrieve_cross_dossier_memories(): query Chroma across dossiers by unit/risk_level metadata.
- build_preference_context(): convert user preferences dict → system prompt snippet.
"""
import logging
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.entities import AgentFeedback, AgentMemory, Dossier
from app.services.memory import vector_store
from app.services.memory.vector_store import _chroma_base, _get_or_create_collection

logger = logging.getLogger(__name__)


async def retrieve_relevant_memories(
    session: AsyncSession,
    dossier_id: int,
    query: str,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Return the most relevant memory chunks for a dossier.

    Primary path: Chroma vector similarity search (WHERE dossier_id=…).
    Degraded path: all PostgreSQL rows for the dossier when Chroma is unreachable.

    Each chunk: {"document": str, "metadata": dict, "source": "chroma"|"pg"}.
    Returns at most `top_k` (or settings.memory_top_k) items.
    """
    cfg = get_settings()
    k = top_k if top_k is not None else cfg.memory_top_k

    # --- Primary: Chroma ---
    chroma_results = await vector_store.query_memories(dossier_id, query, top_k=k)
    if chroma_results:
        logger.debug(
            "Chroma returned %d memory chunks for dossier %d", len(chroma_results), dossier_id
        )
        return [
            {
                "document": r["document"],
                "metadata": r.get("metadata", {}),
                "source": "chroma",
                "distance": r.get("distance"),
            }
            for r in chroma_results
        ]

    # --- Degraded: PostgreSQL fallback ---
    logger.info(
        "Chroma unreachable or empty — falling back to PG rows for dossier %d", dossier_id
    )
    result = await session.execute(
        select(AgentMemory)
        .where(AgentMemory.dossier_id == dossier_id)
        .order_by(AgentMemory.step.asc())
    )
    rows = list(result.scalars().all())
    chunks = [
        {
            "document": f"[Step {m.step}] Thought: {m.thought}\nObservation: {m.observation or 'N/A'}",
            "metadata": {
                "dossier_id": dossier_id,
                "step": m.step,
                "tool_name": m.tool_name or "",
            },
            "source": "pg",
            "distance": None,
        }
        for m in rows
    ]
    # Trim to top_k (no ranking available in degraded mode)
    return chunks[-k:] if len(chunks) > k else chunks


async def retrieve_cross_dossier_memories(
    query: str,
    unit: str | None = None,
    risk_level: str | None = None,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """T-16: Query Chroma across ALL dossiers, optionally filtered by unit or risk_level.

    Used to surface lessons learned from similar past dossiers for the planner phase.
    Returns [] on Chroma failure (degraded — PG fallback not practical for cross-dossier).
    """
    cfg = get_settings()
    k = top_k if top_k is not None else cfg.memory_top_k

    # Build Chroma where-filter (only add clauses that are specified)
    where: dict[str, Any] | None = None
    clauses: list[dict[str, Any]] = []
    if unit:
        clauses.append({"unit": {"$eq": unit}})
    if risk_level:
        clauses.append({"risk_level": {"$eq": risk_level}})

    if len(clauses) == 1:
        where = clauses[0]
    elif len(clauses) > 1:
        where = {"$and": clauses}

    async with httpx.AsyncClient(timeout=15.0) as client:
        coll_id = await _get_or_create_collection(client, cfg.chroma_collection_memories)
        if not coll_id:
            return []
        try:
            payload: dict[str, Any] = {
                "query_texts": [query],
                "n_results": k,
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                payload["where"] = where

            r = await client.post(
                f"{_chroma_base()}/api/v1/collections/{coll_id}/query",
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            ids = (data.get("ids") or [[]])[0]
            docs = (data.get("documents") or [[]])[0]
            metas = (data.get("metadatas") or [[]])[0]
            dists = (data.get("distances") or [[]])[0]
            return [
                {"document": d, "metadata": m, "distance": dist, "source": "chroma_cross"}
                for _, d, m, dist in zip(ids, docs, metas, dists)
            ]
        except Exception as exc:
            logger.warning("Cross-dossier Chroma query failed (degraded): %s", exc)
            return []


def build_preference_context(preferences: dict[str, Any]) -> str:
    """T-16: Convert a user-preferences dict into a system-prompt snippet.

    Called by react_agent to inject personalization into the agent's system prompt
    when a user_id is provided to the appraise endpoint.

    Supported keys:
      report_style: "concise" | "detailed"
      language: "vi" | "en"
      risk_focus: "financial" | "legal" | "all"
    """
    if not preferences:
        return ""

    lines: list[str] = ["## User Preferences (personalize your response accordingly)"]

    style = preferences.get("report_style")
    if style == "concise":
        lines.append("- Report style: CONCISE — use bullet points, max 3 sentences per section.")
    elif style == "detailed":
        lines.append("- Report style: DETAILED — include full analysis, cite all checked items.")

    lang = preferences.get("language", "vi")
    if lang == "en":
        lines.append("- Language: respond in English.")
    else:
        lines.append("- Language: respond in Vietnamese (tiếng Việt).")

    focus = preferences.get("risk_focus")
    if focus == "financial":
        lines.append("- Risk focus: prioritize ERP financial checks (budget, inventory).")
    elif focus == "legal":
        lines.append("- Risk focus: prioritize legal document checks (LegalGraphRAG).")

    return "\n".join(lines)


async def retrieve_feedback_lessons(
    query: str,
    unit: str | None = None,
    top_k: int | None = None,
    session: AsyncSession | None = None,
) -> list[dict[str, Any]]:
    """T-20: Retrieve past negative-feedback lessons from Chroma before planning.

    Degraded path: recent reject/adjust rows from PostgreSQL when Chroma is unreachable.
    """
    cfg = get_settings()
    k = top_k if top_k is not None else cfg.memory_top_k

    chroma_lessons = await vector_store.query_feedback_lessons(query, unit=unit, top_k=k)
    if chroma_lessons:
        logger.debug("Retrieved %d feedback lessons from Chroma for unit=%s", len(chroma_lessons), unit)
        return [
            {
                "document": r["document"],
                "metadata": r.get("metadata", {}),
                "source": "chroma_feedback",
                "distance": r.get("distance"),
            }
            for r in chroma_lessons
        ]

    if not session:
        return []

    logger.info("Chroma feedback_lessons empty — PG fallback for unit=%s", unit)
    stmt = (
        select(AgentFeedback, Dossier.doc_no, Dossier.title)
        .join(Dossier, AgentFeedback.dossier_id == Dossier.id)
        .where(AgentFeedback.feedback_type.in_(["reject", "adjust"]))
        .order_by(AgentFeedback.created_at.desc())
        .limit(k)
    )
    if unit:
        stmt = stmt.where(Dossier.unit == unit)

    result = await session.execute(stmt)
    rows = result.all()
    return [
        {
            "document": (
                f"[PG feedback — {fb.feedback_type}] Dossier {doc_no}: {title}. "
                f"Comment: {fb.comment or 'N/A'}"
            ),
            "metadata": {"dossier_id": fb.dossier_id, "feedback_type": fb.feedback_type},
            "source": "pg_feedback",
            "distance": None,
        }
        for fb, doc_no, title in rows
    ]


def build_feedback_lessons_context(lessons: list[dict[str, Any]]) -> str:
    """Format feedback lessons for injection into the planner system prompt."""
    if not lessons:
        return ""
    lines = ["## Lessons from past user feedback (avoid repeating these mistakes)"]
    for i, lesson in enumerate(lessons, 1):
        lines.append(f"{i}. {lesson['document']}")
    return "\n".join(lines)
