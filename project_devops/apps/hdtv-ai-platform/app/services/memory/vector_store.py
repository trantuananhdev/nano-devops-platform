"""T-15: Vector Memory Service — Chroma HTTP client for agent_memories collection.

Uses Chroma REST API (no embed SDK import) so it works as pure HTTP client
against the existing chroma container on Alpine VM.  Falls back gracefully
when Chroma is unreachable so the appraisal loop never raises 500.
"""
import logging
import time
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _chroma_base() -> str:
    cfg = get_settings()
    return f"http://{cfg.chroma_host}:{cfg.chroma_port}"


async def _get_or_create_collection(client: httpx.AsyncClient, name: str) -> str | None:
    """Return the Chroma collection UUID; create if absent. Returns None on error."""
    base = _chroma_base()
    try:
        r = await client.post(
            f"{base}/api/v1/collections",
            json={"name": name, "get_or_create": True},
            timeout=10.0,
        )
        r.raise_for_status()
        return r.json().get("id") or name
    except Exception as exc:
        logger.warning("Chroma get_or_create collection '%s' failed: %s", name, exc)
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def upsert_memory(
    dossier_id: int,
    step: int,
    thought: str,
    observation: str | None,
    tool_name: str | None = None,
    memory_id: str | None = None,
) -> str | None:
    """Upsert one agent memory step into Chroma.

    Returns the Chroma document id on success, None on failure (degraded).
    The id is stored back in AgentMemory.embedding_id for later retrieval.
    """
    cfg = get_settings()
    doc_id = memory_id or f"mem-{dossier_id}-{step}-{int(time.time())}"
    document = f"[Step {step}] Thought: {thought}\nObservation: {observation or 'N/A'}"
    metadata: dict[str, Any] = {
        "dossier_id": dossier_id,
        "step": step,
        "tool_name": tool_name or "",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        coll_id = await _get_or_create_collection(client, cfg.chroma_collection_memories)
        if not coll_id:
            logger.warning("Skipping Chroma upsert (collection unavailable)")
            return None
        try:
            base = _chroma_base()
            r = await client.post(
                f"{base}/api/v1/collections/{coll_id}/upsert",
                json={
                    "ids": [doc_id],
                    "documents": [document],
                    "metadatas": [metadata],
                },
            )
            r.raise_for_status()
            logger.debug("Chroma upsert ok: %s", doc_id)
            return doc_id
        except Exception as exc:
            logger.warning("Chroma upsert failed (degraded): %s", exc)
            return None


async def query_memories(
    dossier_id: int,
    query_text: str,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Query Chroma for the top-k most relevant memory chunks for a dossier.

    Returns list of {"id", "document", "metadata", "distance"}.
    Returns [] on failure (degraded mode — caller must handle).
    """
    cfg = get_settings()
    k = top_k if top_k is not None else cfg.memory_top_k

    async with httpx.AsyncClient(timeout=15.0) as client:
        coll_id = await _get_or_create_collection(client, cfg.chroma_collection_memories)
        if not coll_id:
            return []
        try:
            base = _chroma_base()
            r = await client.post(
                f"{base}/api/v1/collections/{coll_id}/query",
                json={
                    "query_texts": [query_text],
                    "n_results": k,
                    "where": {"dossier_id": dossier_id},
                    "include": ["documents", "metadatas", "distances"],
                },
            )
            r.raise_for_status()
            data = r.json()
            # Flatten the nested list returned by Chroma
            ids = (data.get("ids") or [[]])[0]
            docs = (data.get("documents") or [[]])[0]
            metas = (data.get("metadatas") or [[]])[0]
            dists = (data.get("distances") or [[]])[0]
            return [
                {"id": i, "document": d, "metadata": m, "distance": dist}
                for i, d, m, dist in zip(ids, docs, metas, dists)
            ]
        except Exception as exc:
            logger.warning("Chroma query failed (degraded): %s", exc)
            return []


async def upsert_feedback_lesson(
    feedback_id: int,
    dossier_id: int,
    document: str,
    *,
    unit: str | None = None,
    feedback_type: str = "reject",
) -> str | None:
    """T-20: Upsert negative feedback lesson into Chroma feedback_lessons collection."""
    cfg = get_settings()
    doc_id = f"fb-{feedback_id}"
    metadata: dict[str, Any] = {
        "feedback_id": feedback_id,
        "dossier_id": dossier_id,
        "feedback_type": feedback_type,
        "unit": unit or "",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        coll_id = await _get_or_create_collection(client, cfg.chroma_collection_feedback_lessons)
        if not coll_id:
            return None
        try:
            base = _chroma_base()
            r = await client.post(
                f"{base}/api/v1/collections/{coll_id}/upsert",
                json={
                    "ids": [doc_id],
                    "documents": [document],
                    "metadatas": [metadata],
                },
            )
            r.raise_for_status()
            logger.debug("Chroma feedback_lesson upsert ok: %s", doc_id)
            return doc_id
        except Exception as exc:
            logger.warning("Chroma feedback_lesson upsert failed (degraded): %s", exc)
            return None


async def query_feedback_lessons(
    query_text: str,
    *,
    unit: str | None = None,
    top_k: int | None = None,
) -> list[dict[str, Any]]:
    """Query feedback_lessons collection; returns [] on failure (degraded)."""
    cfg = get_settings()
    k = top_k if top_k is not None else cfg.memory_top_k

    where: dict[str, Any] | None = None
    if unit:
        where = {"unit": {"$eq": unit}}

    async with httpx.AsyncClient(timeout=15.0) as client:
        coll_id = await _get_or_create_collection(client, cfg.chroma_collection_feedback_lessons)
        if not coll_id:
            return []
        try:
            base = _chroma_base()
            payload: dict[str, Any] = {
                "query_texts": [query_text],
                "n_results": k,
                "include": ["documents", "metadatas", "distances"],
            }
            if where:
                payload["where"] = where
            r = await client.post(
                f"{base}/api/v1/collections/{coll_id}/query",
                json=payload,
            )
            r.raise_for_status()
            data = r.json()
            ids = (data.get("ids") or [[]])[0]
            docs = (data.get("documents") or [[]])[0]
            metas = (data.get("metadatas") or [[]])[0]
            dists = (data.get("distances") or [[]])[0]
            return [
                {"id": i, "document": d, "metadata": m, "distance": dist}
                for i, d, m, dist in zip(ids, docs, metas, dists)
            ]
        except Exception as exc:
            logger.warning("Chroma feedback_lessons query failed (degraded): %s", exc)
            return []


async def count_feedback_lessons() -> int:
    """Return document count in feedback_lessons collection; 0 on failure."""
    cfg = get_settings()
    async with httpx.AsyncClient(timeout=10.0) as client:
        coll_id = await _get_or_create_collection(client, cfg.chroma_collection_feedback_lessons)
        if not coll_id:
            return 0
        try:
            base = _chroma_base()
            r = await client.get(f"{base}/api/v1/collections/{coll_id}/count")
            r.raise_for_status()
            return int(r.json())
        except Exception as exc:
            logger.warning("Chroma feedback_lessons count failed (degraded): %s", exc)
            return 0


# ---------------------------------------------------------------------------
# T-27: Legal docs collection (RAG pipeline ingested documents)
# ---------------------------------------------------------------------------

async def upsert_legal_doc(
    doc_id: str,
    text: str,
    metadata: dict[str, Any],
) -> bool:
    """Upsert a legal document chunk into the legal_docs Chroma collection.

    Args:
        doc_id:   Unique identifier for this chunk (e.g. "legal-decree-0")
        text:     Chunk text content
        metadata: Dict with source, chunk_idx, ingested_at, etc.

    Returns:
        True on success, False on degraded fallback.
    """
    cfg = get_settings()
    async with httpx.AsyncClient(timeout=15.0) as client:
        coll_id = await _get_or_create_collection(client, cfg.rag_legal_collection)
        if not coll_id:
            logger.warning("Chroma upsert_legal_doc: collection unavailable — skipping")
            return False
        try:
            base = _chroma_base()
            r = await client.post(
                f"{base}/api/v1/collections/{coll_id}/upsert",
                json={
                    "ids":       [doc_id],
                    "documents": [text],
                    "metadatas": [metadata],
                },
            )
            r.raise_for_status()
            logger.debug("Chroma upsert_legal_doc ok: %s", doc_id)
            return True
        except Exception as exc:
            logger.warning("Chroma upsert_legal_doc failed (degraded): %s", exc)
            return False


async def query_legal_docs(
    query: str,
    top_k: int = 3,
) -> list[dict[str, Any]]:
    """Query the legal_docs Chroma collection (T-27 RAG pipeline).

    Args:
        query:  Natural language or keyword query
        top_k:  Max number of results to return

    Returns:
        List of {"id", "document", "metadata", "distance"} dicts.
        Returns [] on Chroma unavailability (degraded mode).
    """
    cfg = get_settings()
    async with httpx.AsyncClient(timeout=15.0) as client:
        coll_id = await _get_or_create_collection(client, cfg.rag_legal_collection)
        if not coll_id:
            return []
        try:
            base = _chroma_base()
            r = await client.post(
                f"{base}/api/v1/collections/{coll_id}/query",
                json={
                    "query_texts": [query],
                    "n_results":   top_k,
                    "include":     ["documents", "metadatas", "distances"],
                },
            )
            r.raise_for_status()
            data = r.json()
            ids   = (data.get("ids")       or [[]])[0]
            docs  = (data.get("documents") or [[]])[0]
            metas = (data.get("metadatas") or [[]])[0]
            dists = (data.get("distances") or [[]])[0]
            return [
                {"id": i, "document": d, "metadata": m, "distance": dist}
                for i, d, m, dist in zip(ids, docs, metas, dists)
            ]
        except Exception as exc:
            logger.warning("Chroma query_legal_docs failed (degraded): %s", exc)
            return []
