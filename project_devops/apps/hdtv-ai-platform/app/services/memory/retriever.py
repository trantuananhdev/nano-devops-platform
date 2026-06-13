"""T-15 / T-16: Memory Retriever — retrieve_relevant_memories() + cross-dossier support.

Strategy:
1. Try Chroma vector query (top_k chunks) with dossier-scoped WHERE filter.
2. Degrade: if Chroma unreachable or empty, load recent PG rows for dossier.

Scoring improvements (beyond basic vector distance):
- Recency weighting: recent steps are more relevant (exponential decay)
- Failure boost: failure observations are more informative than successes
- Final score = relevance × 0.6 + recency × 0.3 + failure_boost × 0.1

T-16 additions:
- retrieve_cross_dossier_memories(): semantic search across all dossiers.
- build_preference_context(): user preferences → system prompt snippet.
- retrieve_feedback_lessons(): past feedback → planner injection.
"""
import logging
import math
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.models.entities import AgentFeedback, AgentMemory, Dossier
from app.services.memory import vector_store
from app.services.memory.vector_store import _chroma_base, _get_or_create_collection

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Internal scoring helpers
# ---------------------------------------------------------------------------

def _recency_score(step: int, current_step: int) -> float:
    """Exponential decay: recent steps score closer to 1.0.
    Half-life ≈ 5 steps.
    """
    age = max(0, current_step - step)
    return math.exp(-age * 0.14)  # e^(-0.14*5) ≈ 0.5


def _failure_boost(document: str) -> float:
    """Failures contain more diagnostic information — small upward boost."""
    doc_lower = document.lower()
    failure_keywords = ("fail", "error", "lỗi", "không đạt", "vượt", "thiếu", "cảnh báo", "warning")
    return 0.15 if any(kw in doc_lower for kw in failure_keywords) else 0.0


def _score_chunk(chunk: dict[str, Any], current_step: int) -> float:
    """Combined relevance + recency + failure score.

    distance: Chroma cosine distance (lower = more similar, range 0-2).
    We convert to relevance = 1 - (distance / 2).
    """
    distance = chunk.get("distance")
    if distance is None:
        relevance = 0.5  # unknown similarity → neutral
    else:
        relevance = max(0.0, 1.0 - (distance / 2.0))

    step = chunk.get("metadata", {}).get("step", 0)
    recency = _recency_score(step, current_step)

    failure = _failure_boost(chunk.get("document", ""))

    return relevance * 0.6 + recency * 0.3 + failure * 0.1


# ---------------------------------------------------------------------------
# Primary retrieval
# ---------------------------------------------------------------------------

async def retrieve_relevant_memories(
    session: AsyncSession,
    dossier_id: int,
    query: str,
    top_k: int | None = None,
    current_step: int = 0,
) -> list[dict[str, Any]]:
    """Return the most relevant memory chunks for a dossier.

    Primary path: Chroma vector similarity search, re-ranked by composite score.
    Degraded path: recent PostgreSQL rows for the dossier.

    Each chunk: {"document": str, "metadata": dict, "score": float, "source": str}.
    Returns at most `top_k` (or settings.memory_top_k) items, highest score first.
    """
    cfg = get_settings()
    k = top_k if top_k is not None else cfg.memory_top_k

    # Fetch more candidates than needed so re-ranking can select best k
    fetch_k = min(k * 3, 30)

    chroma_results = await vector_store.query_memories(dossier_id, query, top_k=fetch_k)
    if chroma_results:
        logger.debug(
            "Chroma returned %d memory candidates for dossier %d (will re-rank to top %d)",
            len(chroma_results), dossier_id, k,
        )
        chunks = [
            {
                "document": r["document"],
                "metadata": r.get("metadata", {}),
                "source": "chroma",
                "distance": r.get("distance"),
                "score": 0.0,  # filled below
            }
            for r in chroma_results
        ]
        # Re-rank by composite score
        for c in chunks:
            c["score"] = _score_chunk(c, current_step)
        chunks.sort(key=lambda x: x["score"], reverse=True)
        return chunks[:k]

    # --- Degraded: PostgreSQL fallback ---
    logger.info("Chroma unreachable/empty — PG fallback for dossier %d", dossier_id)
    result = await session.execute(
        select(AgentMemory)
        .where(AgentMemory.dossier_id == dossier_id)
        .order_by(AgentMemory.step.desc())
        .limit(k)
    )
    rows = list(result.scalars().all())
    chunks = [
        {
            "document": (
                f"[Step {m.step}] "
                f"Action: {m.action} | Tool: {m.tool_name or 'N/A'}\n"
                f"Thought: {m.thought}\n"
                f"Observation: {m.observation or 'N/A'}"
            ),
            "metadata": {
                "dossier_id": dossier_id,
                "step": m.step,
                "tool_name": m.tool_name or "",
                "action": m.action,
            },
            "source": "pg",
            "distance": None,
            "score": _recency_score(m.step, current_step) + _failure_boost(m.observation or ""),
        }
        for m in rows
    ]
    chunks.sort(key=lambda x: x["score"], reverse=True)
    return chunks


# ---------------------------------------------------------------------------
# Cross-dossier retrieval (T-16)
# ---------------------------------------------------------------------------

async def retrieve_cross_dossier_memories(
    query: str,
    unit: str | None = None,
    risk_level: str | None = None,
    top_k: int | None = None,
    current_step: int = 0,
) -> list[dict[str, Any]]:
    """T-16: Query Chroma across ALL dossiers, filtered by unit or risk_level.

    Used to surface lessons learned from similar past dossiers for the planner.
    Returns [] on Chroma failure.
    """
    cfg = get_settings()
    k = top_k if top_k is not None else cfg.memory_top_k

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

    fetch_k = min(k * 3, 30)

    async with httpx.AsyncClient(timeout=15.0) as client:
        coll_id = await _get_or_create_collection(client, cfg.chroma_collection_memories)
        if not coll_id:
            return []
        try:
            payload: dict[str, Any] = {
                "query_texts": [query],
                "n_results": fetch_k,
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
            ids   = (data.get("ids")       or [[]])[0]
            docs  = (data.get("documents") or [[]])[0]
            metas = (data.get("metadatas") or [[]])[0]
            dists = (data.get("distances") or [[]])[0]

            chunks = [
                {
                    "document": d,
                    "metadata": m,
                    "distance": dist,
                    "source": "chroma_cross",
                    "score": 0.0,
                }
                for _, d, m, dist in zip(ids, docs, metas, dists)
            ]
            for c in chunks:
                c["score"] = _score_chunk(c, current_step)
            chunks.sort(key=lambda x: x["score"], reverse=True)
            return chunks[:k]

        except Exception as exc:
            logger.warning("Cross-dossier Chroma query failed (degraded): %s", exc)
            return []


# ---------------------------------------------------------------------------
# Preference context builder (T-16)
# ---------------------------------------------------------------------------

def build_preference_context(preferences: dict[str, Any]) -> str:
    """T-16: Convert user preferences dict → system prompt snippet.

    Supported keys:
      report_style: "concise" | "detailed"
      language: "vi" | "en"
      risk_focus: "financial" | "legal" | "technical" | "all"
      output_format: "markdown" | "table" | "bullets"
    """
    if not preferences:
        return ""

    lines: list[str] = ["## User Preferences (apply throughout your response)"]

    style = preferences.get("report_style")
    if style == "concise":
        lines.append("- Report style: CONCISE — bullet points, max 3 sentences per section, omit obvious.")
    elif style == "detailed":
        lines.append("- Report style: DETAILED — full analysis, cite all items, explain reasoning.")

    lang = preferences.get("language", "vi")
    if lang == "en":
        lines.append("- Language: respond in English.")
    else:
        lines.append("- Language: respond in Vietnamese (tiếng Việt).")

    focus = preferences.get("risk_focus")
    if focus == "financial":
        lines.append("- Risk focus: prioritize financial checks (budget, inventory, price anomaly).")
    elif focus == "legal":
        lines.append("- Risk focus: prioritize legal document checks (authorization, citations).")
    elif focus == "technical":
        lines.append("- Risk focus: prioritize technical standard checks (specs, certification).")

    fmt = preferences.get("output_format")
    if fmt == "table":
        lines.append("- Output format: use Markdown tables for check results.")
    elif fmt == "bullets":
        lines.append("- Output format: use bullet points throughout, no prose paragraphs.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Feedback lessons (T-20)
# ---------------------------------------------------------------------------

async def retrieve_feedback_lessons(
    query: str,
    unit: str | None = None,
    top_k: int | None = None,
    session: AsyncSession | None = None,
) -> list[dict[str, Any]]:
    """T-20: Retrieve past negative-feedback lessons from Chroma before planning.

    These lessons teach the planner to avoid previously flagged mistakes.
    Degraded path: recent reject/adjust rows from PostgreSQL.
    """
    cfg = get_settings()
    k = top_k if top_k is not None else cfg.memory_top_k

    chroma_lessons = await vector_store.query_feedback_lessons(query, unit=unit, top_k=k)
    if chroma_lessons:
        logger.debug("Retrieved %d feedback lessons from Chroma (unit=%s)", len(chroma_lessons), unit)
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

    logger.info("Chroma feedback_lessons empty — PG fallback (unit=%s)", unit)
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
                f"[Feedback {fb.feedback_type.upper()}] Dossier {doc_no}: {title}. "
                f"User comment: {fb.comment or 'N/A'}. "
                f"Lesson: Avoid repeating this issue in future appraisals of similar dossiers."
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
    lines = ["## Lessons from past user feedback (IMPORTANT: avoid these mistakes)"]
    for i, lesson in enumerate(lessons, 1):
        lines.append(f"{i}. {lesson['document']}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Memory context formatter
# ---------------------------------------------------------------------------

def build_memory_context(memories: list[dict[str, Any]], max_chunks: int = 5) -> str:
    """Format retrieved memories into a compact context block for the planner.

    Prioritizes high-scoring chunks. Each chunk gets a brief header.
    """
    if not memories:
        return ""

    top = memories[:max_chunks]
    lines = ["## Relevant memories from similar past steps (use as context, not as facts)"]
    for i, m in enumerate(top, 1):
        score = m.get("score", 0.0)
        source = m.get("source", "unknown")
        doc = m.get("document", "").strip()
        # Truncate very long documents
        if len(doc) > 400:
            doc = doc[:400] + "… [truncated]"
        lines.append(f"{i}. [{source} | score={score:.2f}] {doc}")
    return "\n".join(lines)
