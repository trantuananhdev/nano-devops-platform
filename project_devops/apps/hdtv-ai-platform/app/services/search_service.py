"""T-11: Meilisearch full-text search service.

Design decisions:
- Pure httpx (async) — no meilisearch-python SDK to keep requirements minimal.
- Graceful degradation: if Meilisearch is unreachable, returns empty results
  rather than raising 500. Search is a convenience feature, not a blocker.
- Indexing is fire-and-forget (background task) so POST /appraise is not delayed.
- All config via Settings (ENV).
"""

import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def dossier_to_doc(dossier: Any) -> dict[str, Any]:
    """Map a Dossier ORM row to a Meilisearch document."""
    risk = dossier.risk_level.value if hasattr(dossier.risk_level, "value") else str(dossier.risk_level)
    status = dossier.status.value if hasattr(dossier.status, "value") else str(dossier.status)
    return {
        "id": dossier.id,
        "doc_no": dossier.doc_no,
        "title": dossier.title,
        "unit": dossier.unit,
        "risk_level": risk,
        "status": status,
        "created_at": dossier.created_at.isoformat() if dossier.created_at else None,
    }

_INDEX_SETTINGS = {
    "searchableAttributes": ["title", "doc_no", "unit", "risk_level", "status"],
    "filterableAttributes": ["risk_level", "status", "unit"],
    "sortableAttributes": ["created_at", "id"],
    "displayedAttributes": ["id", "doc_no", "title", "unit", "risk_level", "status", "created_at"],
}


def _meili_headers() -> dict[str, str]:
    s = get_settings()
    h = {"Content-Type": "application/json"}
    if s.meili_api_key:
        h["Authorization"] = f"Bearer {s.meili_api_key}"
    return h


def _meili_base() -> str:
    return get_settings().meili_url.rstrip("/")


def _index_name() -> str:
    return get_settings().meili_index_dossiers


async def ensure_index() -> None:
    """Create index and configure settings. Called once on startup."""
    base = _meili_base()
    idx = _index_name()
    headers = _meili_headers()

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            # Create index (idempotent — 200 if exists)
            await client.post(
                f"{base}/indexes",
                headers=headers,
                json={"uid": idx, "primaryKey": "id"},
            )
            # Configure settings
            await client.patch(
                f"{base}/indexes/{idx}/settings",
                headers=headers,
                json=_INDEX_SETTINGS,
            )
            logger.info("Meilisearch index '%s' ready", idx)
        except Exception as exc:
            logger.warning("Meilisearch ensure_index failed (will retry): %s", exc)


async def index_dossier(dossier: dict[str, Any]) -> None:
    """Upsert a single dossier document into Meilisearch index."""
    base = _meili_base()
    idx = _index_name()
    headers = _meili_headers()

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            await client.post(
                f"{base}/indexes/{idx}/documents",
                headers=headers,
                json=[dossier],
            )
        except Exception as exc:
            logger.warning("Meilisearch index_dossier failed for id=%s: %s", dossier.get("id"), exc)


async def index_all_dossiers(dossiers: list[dict[str, Any]]) -> None:
    """Bulk-upsert all dossiers (called on seed / startup warm-up)."""
    if not dossiers:
        return
    base = _meili_base()
    idx = _index_name()
    headers = _meili_headers()

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            await client.post(
                f"{base}/indexes/{idx}/documents",
                headers=headers,
                json=dossiers,
            )
            logger.info("Meilisearch: indexed %d dossiers", len(dossiers))
        except Exception as exc:
            logger.warning("Meilisearch bulk index failed: %s", exc)


async def search_dossiers(
    query: str,
    *,
    filter_risk: str | None = None,
    filter_status: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, Any]:
    """Full-text search dossiers. Returns Meilisearch hits or empty result on error."""
    base = _meili_base()
    idx = _index_name()
    headers = _meili_headers()

    filters: list[str] = []
    if filter_risk:
        filters.append(f"risk_level = {filter_risk}")
    if filter_status:
        filters.append(f"status = {filter_status}")

    body: dict[str, Any] = {
        "q": query,
        "limit": limit,
        "offset": offset,
        "attributesToHighlight": ["title", "doc_no"],
        "highlightPreTag": "<mark>",
        "highlightPostTag": "</mark>",
    }
    if filters:
        body["filter"] = " AND ".join(filters)

    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            resp = await client.post(
                f"{base}/indexes/{idx}/search",
                headers=headers,
                json=body,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as exc:
            logger.warning("Meilisearch search failed for q='%s': %s", query, exc)
            return {
                "hits": [],
                "query": query,
                "processingTimeMs": 0,
                "estimatedTotalHits": 0,
                "_degraded": True,
            }
