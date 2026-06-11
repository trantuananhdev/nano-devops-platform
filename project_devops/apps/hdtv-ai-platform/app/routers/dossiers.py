import time
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.entities import AiAuditLog, Dossier
from app.schemas.dossier import (
    AppraiseRequest,
    AppraiseResponse,
    DossierCreate,
    DossierDetail,
    DossierOut,
    DossierPage,
    PdfUrlOut,
    UploadResult,
)
from app.services.dossier_service import (
    count_dossiers,
    create_dossier,
    get_dossier_detail,
    list_dossiers,
    update_pdf_url,
)
from app.services import minio_service, search_service
from app.workers.tasks import run_appraisal_task

router = APIRouter()

_MAX_PDF_BYTES = 20 * 1024 * 1024  # 20MB


@router.get("", response_model=DossierPage)
async def get_dossiers(
    offset: int = Query(default=0, ge=0, description="Skip N rows"),
    limit: int = Query(default=20, ge=1, le=200, description="Max rows (default 20, max 200)"),
    session: AsyncSession = Depends(get_db),
) -> DossierPage:
    """T-40: Paginated dossier list.

    Returns DossierPage with items, total, offset, limit, has_more.
    FE stores use offset-based pagination: load first page on mount,
    then append pages on demand (infinite scroll / load-more).
    """
    items = await list_dossiers(session, offset=offset, limit=limit)
    total = await count_dossiers(session)
    return DossierPage(
        items=items,
        total=total,
        offset=offset,
        limit=limit,
        has_more=(offset + len(items)) < total,
    )


@router.post("", response_model=DossierOut, status_code=status.HTTP_201_CREATED)
async def create_new_dossier(
    body: DossierCreate,
    session: AsyncSession = Depends(get_db),
) -> DossierOut:
    """T-13: Create a new dossier.

    - Validates doc_no uniqueness (409 if duplicate)
    - Logs DossierCreate to ai_audit_logs
    - Indexes in Meilisearch so it's immediately searchable
    """
    t0 = time.monotonic()
    try:
        dossier = await create_dossier(session, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))

    # Audit log
    session.add(AiAuditLog(
        task_id=str(uuid.uuid4()),
        tool_name="DossierCreate",
        execution_time_ms=int((time.monotonic() - t0) * 1000),
        inputs=body.model_dump(),
        outputs={"dossier_id": dossier.id, "doc_no": dossier.doc_no},
    ))
    await session.commit()

    await search_service.index_dossier(search_service.dossier_to_doc(dossier))

    return DossierOut.model_validate(dossier)


@router.get("/{dossier_id}", response_model=DossierDetail)
async def get_dossier(
    dossier_id: int,
    session: AsyncSession = Depends(get_db),
) -> DossierDetail:
    detail = await get_dossier_detail(session, dossier_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Dossier not found")
    return detail


@router.get("/{dossier_id}/pdf-url", response_model=PdfUrlOut)
async def get_dossier_pdf_url(
    dossier_id: int,
    session: AsyncSession = Depends(get_db),
) -> PdfUrlOut:
    """T-14: Return a fresh presigned MinIO URL for the uploaded PDF (1h TTL)."""
    detail = await get_dossier_detail(session, dossier_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Dossier not found")
    if not detail.pdf_url:
        raise HTTPException(status_code=404, detail="No PDF uploaded for this dossier")

    url = await minio_service.get_presigned_url(detail.pdf_url)
    if not url:
        raise HTTPException(status_code=503, detail="Object storage unavailable")

    return PdfUrlOut(dossier_id=dossier_id, pdf_url=url, expires_in=3600)


@router.post(
    "/{dossier_id}/upload",
    response_model=UploadResult,
    summary="Upload PDF file to MinIO and attach to dossier",
)
async def upload_pdf(
    dossier_id: int,
    file: UploadFile = File(..., description="PDF file (max 20MB)"),
    session: AsyncSession = Depends(get_db),
) -> UploadResult:
    """T-13: Upload PDF to MinIO, update dossier.pdf_url, log to audit.

    - Returns presigned URL valid for 1 hour
    - dossier.pdf_url stores internal key for future presigned URL generation
    - Logs PdfUpload to ai_audit_logs
    """
    detail = await get_dossier_detail(session, dossier_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Dossier not found")

    # Validate content type
    ct = file.content_type or ""
    if ct not in ("application/pdf", "application/octet-stream", ""):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are accepted",
        )

    data = await file.read()
    if len(data) > _MAX_PDF_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds 20MB limit",
        )

    t0 = time.monotonic()
    result = await minio_service.upload_pdf(data, file.filename or "upload.pdf")
    elapsed_ms = int((time.monotonic() - t0) * 1000)

    # Update dossier pdf_url → store MinIO key (not presigned URL which expires)
    if result["ok"] and result["key"]:
        await update_pdf_url(session, dossier_id, result["key"])

    # Audit log — every tool call rule
    session.add(AiAuditLog(
        task_id=str(uuid.uuid4()),
        tool_name="PdfUpload",
        execution_time_ms=elapsed_ms,
        inputs={
            "dossier_id": dossier_id,
            "filename": file.filename,
            "size_bytes": len(data),
        },
        outputs={
            "key": result.get("key", ""),
            "ok": result.get("ok", False),
            "error": result.get("error"),
        },
    ))
    await session.commit()

    return UploadResult(
        dossier_id=dossier_id,
        pdf_key=result.get("key", ""),
        pdf_url=result.get("url", ""),
        ok=result.get("ok", False),
        error=result.get("error"),
    )


@router.post("/{dossier_id}/appraise", response_model=AppraiseResponse, status_code=status.HTTP_202_ACCEPTED)
async def appraise_dossier(
    dossier_id: int,
    session: AsyncSession = Depends(get_db),
    user_id: int | None = Query(
        default=None,
        description="Optional user ID for role-based agent profile (T-23)",
    ),
    body: AppraiseRequest | None = None,
) -> AppraiseResponse:
    """Start appraisal; user_id from JSON body takes precedence over query param."""
    detail = await get_dossier_detail(session, dossier_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Dossier not found")
    effective_user_id = body.user_id if body and body.user_id is not None else user_id
    task = run_appraisal_task.delay(dossier_id, effective_user_id)
    return AppraiseResponse(task_id=task.id, dossier_id=dossier_id, status="queued")


@router.get("/units", response_model=list[str])
async def get_dossier_units(
    session: AsyncSession = Depends(get_db),
) -> list[str]:
    """Return distinct unit values from all dossiers for FE filter dropdowns.

    Returns a sorted list of unique unit strings so the filter select is always
    up-to-date without requiring FE code changes when new units are added.
    """
    result = await session.execute(
        select(Dossier.unit).distinct().order_by(Dossier.unit)
    )
    return [row[0] for row in result.all() if row[0]]
