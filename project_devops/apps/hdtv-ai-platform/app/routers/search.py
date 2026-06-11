"""T-11: Full-text search router — GET /api/v1/search."""

from fastapi import APIRouter, Query
from pydantic import BaseModel
from typing import Any

from app.services import search_service

router = APIRouter()


class SearchHit(BaseModel):
    id: int
    doc_no: str
    title: str
    unit: str
    risk_level: str
    status: str
    created_at: str | None = None
    _formatted: dict[str, Any] | None = None


class SearchResponse(BaseModel):
    hits: list[dict[str, Any]]
    query: str
    processing_time_ms: int
    estimated_total_hits: int
    degraded: bool = False


@router.get("/search", response_model=SearchResponse, summary="Full-text dossier search")
async def search_dossiers(
    q: str = Query(default="", description="Search query string"),
    risk: str | None = Query(default=None, description="Filter by risk_level: high|medium|low"),
    status: str | None = Query(default=None, description="Filter by status"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> SearchResponse:
    result = await search_service.search_dossiers(
        q,
        filter_risk=risk,
        filter_status=status,
        limit=limit,
        offset=offset,
    )
    return SearchResponse(
        hits=result.get("hits", []),
        query=result.get("query", q),
        processing_time_ms=result.get("processingTimeMs", 0),
        estimated_total_hits=result.get("estimatedTotalHits", 0),
        degraded=result.get("_degraded", False),
    )
