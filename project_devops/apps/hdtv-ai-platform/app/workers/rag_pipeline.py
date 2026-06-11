"""
T-27: RAG Data Ingestion Pipeline — Celery tasks cho tự động embed tài liệu pháp lý.

Pipeline flow:
  1. `ingest_legal_documents(source_dir)` — Celery task (mỗi 6h via beat):
       - Đọc .txt/.md từ /opt/rag-docs/
       - Sliding window chunk (512 tokens, overlap 64)
       - Upsert vào Chroma collection `legal_docs` kèm metadata {source, chunk_idx, ingested_at}
       - Ghi AiAuditLog với tool_name="RagIngest" để trace
  2. `cleanup_stale_embeddings()` — Celery task (daily 02:00 via beat):
       - Xoá docs trong Chroma legal_docs có ingested_at > rag_stale_days ngày

Constraints:
  - Chroma unreachable → log warning + trả về partial count (không raise)
  - Không phụ thuộc ML embedding library — dùng Chroma built-in embedder (sentence-transformers hoặc no-op)
  - Graceful fallback: nếu source_dir không tồn tại → empty ingest, log info
"""

from __future__ import annotations

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.core.config import get_settings
from app.workers.celery_app import celery_app

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Chunking utility (sliding window, no ML deps)
# ---------------------------------------------------------------------------

def _estimate_tokens(text: str) -> int:
    """Heuristic: 1 token ≈ 4 chars (consistent with context_manager)."""
    return max(1, len(text) // 4)


def _sliding_window_chunks(
    text: str,
    chunk_size_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    """Split text into overlapping chunks by token estimate.

    Args:
        text:               Raw source text
        chunk_size_tokens:  Target tokens per chunk
        overlap_tokens:     Token overlap between consecutive chunks

    Returns:
        List of text chunks (non-empty)
    """
    if not text or not text.strip():
        return []

    chars_per_chunk   = chunk_size_tokens * 4   # 4 chars/token heuristic
    chars_per_overlap = overlap_tokens * 4
    step = max(1, chars_per_chunk - chars_per_overlap)

    chunks: list[str] = []
    start = 0
    while start < len(text):
        chunk = text[start : start + chars_per_chunk].strip()
        if chunk:
            chunks.append(chunk)
        start += step
        if start >= len(text):
            break

    return chunks


# ---------------------------------------------------------------------------
# Chroma helpers (pure httpx, no SDK)
# ---------------------------------------------------------------------------

async def _get_or_create_legal_collection(client: Any) -> str | None:
    """Get/create Chroma collection for legal_docs. Returns collection id or None."""
    import httpx
    cfg = get_settings()
    base = f"http://{cfg.chroma_host}:{cfg.chroma_port}"
    try:
        r = await client.post(
            f"{base}/api/v1/collections",
            json={"name": cfg.rag_legal_collection, "get_or_create": True},
            timeout=10.0,
        )
        r.raise_for_status()
        return r.json().get("id") or cfg.rag_legal_collection
    except Exception as exc:
        logger.warning("RAG: Chroma get_or_create '%s' failed: %s", cfg.rag_legal_collection, exc)
        return None


async def _upsert_chunk_to_chroma(
    client: Any,
    coll_id: str,
    doc_id: str,
    chunk_text: str,
    metadata: dict[str, Any],
) -> bool:
    """Upsert a single chunk. Returns True on success."""
    import httpx
    cfg = get_settings()
    base = f"http://{cfg.chroma_host}:{cfg.chroma_port}"
    try:
        r = await client.post(
            f"{base}/api/v1/collections/{coll_id}/upsert",
            json={
                "ids":       [doc_id],
                "documents": [chunk_text],
                "metadatas": [metadata],
            },
            timeout=15.0,
        )
        r.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("RAG: Chroma upsert chunk '%s' failed: %s", doc_id, exc)
        return False


async def _delete_chunk_from_chroma(
    client: Any,
    coll_id: str,
    doc_ids: list[str],
) -> bool:
    """Delete a list of doc_ids from the collection."""
    import httpx
    cfg = get_settings()
    base = f"http://{cfg.chroma_host}:{cfg.chroma_port}"
    try:
        r = await client.post(
            f"{base}/api/v1/collections/{coll_id}/delete",
            json={"ids": doc_ids},
            timeout=10.0,
        )
        r.raise_for_status()
        return True
    except Exception as exc:
        logger.warning("RAG: Chroma delete failed: %s", exc)
        return False


async def _list_all_chunks_with_metadata(
    client: Any,
    coll_id: str,
) -> list[dict[str, Any]]:
    """Return all docs with metadata from the collection (for stale cleanup)."""
    import httpx
    cfg = get_settings()
    base = f"http://{cfg.chroma_host}:{cfg.chroma_port}"
    try:
        r = await client.post(
            f"{base}/api/v1/collections/{coll_id}/get",
            json={"include": ["metadatas"]},
            timeout=30.0,
        )
        r.raise_for_status()
        data = r.json()
        ids    = data.get("ids") or []
        metas  = data.get("metadatas") or []
        return [{"id": i, "metadata": m} for i, m in zip(ids, metas)]
    except Exception as exc:
        logger.warning("RAG: Chroma list all chunks failed: %s", exc)
        return []


# ---------------------------------------------------------------------------
# AiAuditLog helper (best-effort, never raises)
# ---------------------------------------------------------------------------

async def _emit_rag_audit(
    action: str,
    inputs: dict[str, Any],
    outputs: dict[str, Any],
) -> None:
    """Write RAG pipeline action to AiAuditLog for traceability."""
    try:
        from app.core.database import async_session_factory
        from app.models.entities import AiAuditLog
        async with async_session_factory() as session:
            log = AiAuditLog(
                task_id=f"rag-pipeline-{action}",
                tool_name="RagIngest",
                execution_time_ms=0,
                inputs=inputs,
                outputs=outputs,
            )
            session.add(log)
            await session.commit()
    except Exception as exc:
        logger.debug("RAG audit log write failed (non-critical): %s", exc)


# ---------------------------------------------------------------------------
# Core async ingest logic
# ---------------------------------------------------------------------------

async def _async_ingest_legal_documents(source_dir: str) -> dict[str, Any]:
    """Async implementation of document ingestion pipeline.

    Returns summary dict: {files_processed, chunks_upserted, chunks_failed, skipped}
    """
    import httpx

    cfg = get_settings()
    src_path = Path(source_dir)

    if not src_path.exists():
        logger.info("RAG: source_dir '%s' does not exist — empty ingest", source_dir)
        return {"files_processed": 0, "chunks_upserted": 0, "chunks_failed": 0, "skipped": 0}

    # Collect .txt and .md files
    files = list(src_path.glob("**/*.txt")) + list(src_path.glob("**/*.md"))
    if not files:
        logger.info("RAG: no .txt/.md files found in '%s'", source_dir)
        return {"files_processed": 0, "chunks_upserted": 0, "chunks_failed": 0, "skipped": 0}

    chunks_upserted = 0
    chunks_failed   = 0
    files_processed = 0
    ingested_at_ts  = int(time.time())

    async with httpx.AsyncClient(timeout=30.0) as client:
        coll_id = await _get_or_create_legal_collection(client)
        if not coll_id:
            logger.warning("RAG: Chroma unavailable — skipping ingest of %d files", len(files))
            return {
                "files_processed": 0,
                "chunks_upserted": 0,
                "chunks_failed":   len(files),
                "skipped":         len(files),
            }

        for fpath in files:
            try:
                text = fpath.read_text(encoding="utf-8", errors="replace").strip()
                if not text:
                    continue

                chunks = _sliding_window_chunks(
                    text,
                    chunk_size_tokens=cfg.rag_chunk_size_tokens,
                    overlap_tokens=cfg.rag_chunk_overlap_tokens,
                )
                source_name = str(fpath.relative_to(src_path))

                for idx, chunk_text in enumerate(chunks):
                    doc_id = f"legal-{source_name.replace('/', '_').replace(' ', '_')}-{idx}"
                    metadata: dict[str, Any] = {
                        "source":       source_name,
                        "chunk_idx":    idx,
                        "ingested_at":  ingested_at_ts,
                        "char_count":   len(chunk_text),
                    }
                    ok = await _upsert_chunk_to_chroma(client, coll_id, doc_id, chunk_text, metadata)
                    if ok:
                        chunks_upserted += 1
                    else:
                        chunks_failed += 1

                files_processed += 1
                logger.debug("RAG: ingested '%s' (%d chunks)", source_name, len(chunks))

            except Exception as exc:
                logger.warning("RAG: failed to process file '%s': %s", fpath, exc)
                chunks_failed += 1

    summary = {
        "files_processed": files_processed,
        "chunks_upserted": chunks_upserted,
        "chunks_failed":   chunks_failed,
        "skipped":         0,
    }
    logger.info("RAG ingest complete: %s", summary)
    return summary


async def _async_cleanup_stale_embeddings() -> dict[str, Any]:
    """Delete Chroma docs older than rag_stale_days from legal_docs collection."""
    import httpx

    cfg = get_settings()
    cutoff_ts = int(time.time()) - cfg.rag_stale_days * 86400

    async with httpx.AsyncClient(timeout=30.0) as client:
        coll_id = await _get_or_create_legal_collection(client)
        if not coll_id:
            return {"deleted": 0, "error": "Chroma unavailable"}

        all_chunks = await _list_all_chunks_with_metadata(client, coll_id)
        stale_ids = [
            c["id"]
            for c in all_chunks
            if isinstance(c.get("metadata"), dict)
            and int(c["metadata"].get("ingested_at", time.time())) < cutoff_ts
        ]

        if not stale_ids:
            logger.info("RAG cleanup: no stale embeddings (cutoff=%s)", datetime.fromtimestamp(cutoff_ts, tz=timezone.utc).isoformat())
            return {"deleted": 0}

        ok = await _delete_chunk_from_chroma(client, coll_id, stale_ids)
        deleted_count = len(stale_ids) if ok else 0
        logger.info("RAG cleanup: deleted %d stale chunk(s)", deleted_count)
        return {"deleted": deleted_count}


# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------

@celery_app.task(name="ingest_legal_documents", bind=True)
def ingest_legal_documents(self, source_dir: str | None = None) -> dict[str, Any]:
    """Celery task: ingest .txt/.md documents from source_dir into Chroma legal_docs.

    Scheduled via Celery beat every 6 hours.

    Args:
        source_dir: Override directory path (default: settings.rag_docs_dir)

    Returns:
        Summary dict with files_processed, chunks_upserted, chunks_failed
    """
    cfg = get_settings()
    src = source_dir or cfg.rag_docs_dir

    logger.info("RAG ingest_legal_documents started: source_dir=%s", src)

    async def _run() -> dict[str, Any]:
        summary = await _async_ingest_legal_documents(src)
        await _emit_rag_audit("ingest", inputs={"source_dir": src}, outputs=summary)
        return summary

    return asyncio.run(_run())


@celery_app.task(name="cleanup_stale_embeddings", bind=True)
def cleanup_stale_embeddings(self) -> dict[str, Any]:
    """Celery task: remove stale legal_docs embeddings (older than rag_stale_days).

    Scheduled via Celery beat daily at 02:00.

    Returns:
        Dict with count of deleted chunks
    """
    cfg = get_settings()
    logger.info("RAG cleanup_stale_embeddings started (stale_days=%d)", cfg.rag_stale_days)

    async def _run() -> dict[str, Any]:
        result = await _async_cleanup_stale_embeddings()
        await _emit_rag_audit("cleanup", inputs={"stale_days": cfg.rag_stale_days}, outputs=result)
        return result

    return asyncio.run(_run())
