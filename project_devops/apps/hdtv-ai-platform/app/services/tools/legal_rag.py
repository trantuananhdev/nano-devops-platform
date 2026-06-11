"""
T-08 + T-27: LegalGraphRAG tool — truy vấn tài liệu pháp lý EVN.

T-27 addition: sau khi query Chroma `legal_docs` (T-27 RAG pipeline ingested),
merge kết quả với LEGAL_FALLBACK + deduplicate by doc_id / title.
"""
from typing import Any

import httpx

from app.core.config import get_settings

LEGAL_FALLBACK = [
    {
        "title": "Nghị định 15/2021/NĐ-CP",
        "snippet": "Quy định về đấu thầu lựa chọn nhà thầu",
        "status": "valid",
    },
    {
        "title": "Quyết định 143/QĐ-HĐTV",
        "snippet": "Phê duyệt chủ trương đầu tư dự án cáp ngầm",
        "status": "valid",
    },
]


def _deduplicate_results(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Remove duplicate entries by title (case-insensitive). First occurrence wins."""
    seen: set[str] = set()
    unique: list[dict[str, Any]] = []
    for item in results:
        key = item.get("title", "").lower().strip()
        if key and key not in seen:
            seen.add(key)
            unique.append(item)
    return unique


async def legal_graph_rag(params: dict[str, Any]) -> dict[str, Any]:
    """Query ChromaDB for relevant legal documents.

    T-27: queries both the seeded `legal_docs` collection (RAG pipeline)
    and falls back to LEGAL_FALLBACK if Chroma is unavailable.
    Merges + deduplicates results from both sources.

    Args:
        params: {"query": str, "title": str (fallback for query)}

    Returns:
        {"query": str, "results": [{"title", "snippet", "status"}, ...]}
    """
    query = params.get("query", params.get("title", ""))
    settings = get_settings()
    chroma_url = f"http://{settings.chroma_host}:{settings.chroma_port}"

    collected_results: list[dict[str, Any]] = []

    # --- Query seeded legal_docs (legacy collection from T-08) ---
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            coll_resp = await client.post(
                f"{chroma_url}/api/v1/collections",
                json={"name": "legal_docs", "get_or_create": True},
            )
            coll_resp.raise_for_status()
            coll_id = coll_resp.json().get("id", "legal_docs")
            query_resp = await client.post(
                f"{chroma_url}/api/v1/collections/{coll_id}/query",
                json={"query_texts": [query], "n_results": 3},
            )
            if query_resp.status_code == 200:
                data = query_resp.json()
                docs  = data.get("documents", [[]])[0]
                metas = data.get("metadatas", [[]])[0]
                for d, m in zip(docs, metas, strict=False):
                    collected_results.append({
                        "title":   m.get("title", ""),
                        "snippet": d,
                        "status":  m.get("status", "valid"),
                        "_source": "seeded",
                    })
    except Exception:
        pass  # Handled below by fallback

    # --- T-27: Also query RAG pipeline-ingested legal_docs collection ---
    # Uses settings.rag_legal_collection (same name by default, but supports override)
    if settings.rag_legal_collection != "legal_docs":
        try:
            from app.services.memory.vector_store import query_legal_docs
            rag_docs = await query_legal_docs(query, top_k=3)
            for item in rag_docs:
                meta = item.get("metadata") or {}
                collected_results.append({
                    "title":   meta.get("source", f"rag-doc-{item.get('id', '')}"),
                    "snippet": item.get("document", ""),
                    "status":  "valid",
                    "_source": "rag_pipeline",
                })
        except Exception:
            pass
    else:
        # Same collection — already queried above; also attempt rag_pipeline query
        # as a second pass in case rag_pipeline collection has more recent docs
        try:
            from app.services.memory.vector_store import query_legal_docs
            rag_docs = await query_legal_docs(query, top_k=3)
            for item in rag_docs:
                meta = item.get("metadata") or {}
                # Only add if has source metadata (RAG pipeline chunks have this)
                if meta.get("source"):
                    collected_results.append({
                        "title":   meta.get("source", ""),
                        "snippet": item.get("document", ""),
                        "status":  "valid",
                        "_source": "rag_pipeline",
                    })
        except Exception:
            pass

    # Remove internal _source key before returning, deduplicate
    clean_results = [
        {"title": r["title"], "snippet": r["snippet"], "status": r["status"]}
        for r in collected_results
        if r.get("title") or r.get("snippet")
    ]
    clean_results = _deduplicate_results(clean_results)

    # Fall back to static list if nothing retrieved
    if not clean_results:
        clean_results = LEGAL_FALLBACK

    return {"query": query, "results": clean_results[:5]}  # Cap at 5 results
