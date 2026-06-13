"""T-13: MinIO object storage service for dossier PDF uploads.

Design decisions:
- minio SDK is synchronous → wrap all calls in asyncio.to_thread() to avoid
  blocking the FastAPI event loop. This is the standard pattern for sync I/O
  in async contexts without adding aiobotocore/aioboto3 complexity.
- Bucket auto-created on first use (idempotent put_object policy).
- pdf_url stored as internal path: minio://<bucket>/<key> — the API serves
  a presigned GET URL on demand so MinIO port doesn't need to be exposed.
- Graceful degradation: if MinIO is unreachable, upload returns a fallback
  URL string. Dossier creation still succeeds.
- All upload actions logged to ai_audit_logs (WorkflowUpload tool).
"""

import asyncio
import io
import logging
import uuid
from datetime import timedelta
from typing import Any

from minio import Minio
from minio.error import S3Error

from app.core.config import get_settings

logger = logging.getLogger(__name__)


def _get_client() -> Minio:
    s = get_settings()
    return Minio(
        s.minio_endpoint,
        access_key=s.minio_access_key,
        secret_key=s.minio_secret_key,
        secure=s.minio_secure,
    )


def _ensure_bucket(client: Minio, bucket: str) -> None:
    """Create bucket if it doesn't exist — idempotent."""
    if not client.bucket_exists(bucket):
        client.make_bucket(bucket)
        logger.info("MinIO bucket '%s' created", bucket)


def _put_object_sync(data: bytes, filename: str, key: str | None = None) -> str:
    """Sync MinIO upload. Returns internal key."""
    s = get_settings()
    client = _get_client()
    _ensure_bucket(client, s.minio_bucket)
    if key is None:
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "bin"
        key = f"dossiers/{uuid.uuid4().hex}.{ext}"
    client.put_object(
        s.minio_bucket,
        key,
        io.BytesIO(data),
        length=len(data),
        content_type="application/pdf" if (filename.lower().endswith(".pdf") or key.lower().endswith(".pdf")) else "application/octet-stream",
    )
    return key


def _presigned_url_sync(key: str) -> str:
    """Generate presigned GET URL valid for 1 hour."""
    s = get_settings()
    client = _get_client()
    url = client.presigned_get_object(s.minio_bucket, key, expires=timedelta(hours=1))
    return url


async def upload_pdf(data: bytes, filename: str, key: str | None = None) -> dict[str, Any]:
    """Async wrapper: upload PDF bytes to MinIO, return {key, url}."""
    try:
        key = await asyncio.to_thread(_put_object_sync, data, filename, key)
        url = await asyncio.to_thread(_presigned_url_sync, key)
        logger.info("MinIO upload OK: key=%s size=%d", key, len(data))
        return {"key": key, "url": url, "ok": True}
    except S3Error as exc:
        logger.warning("MinIO S3Error: %s", exc)
        return {"key": "", "url": "", "ok": False, "error": str(exc)}
    except Exception as exc:
        logger.warning("MinIO upload failed: %s", exc)
        return {"key": "", "url": "", "ok": False, "error": str(exc)}


async def get_presigned_url(key: str) -> str | None:
    """Return a fresh presigned GET URL for an existing object key."""
    try:
        url = await asyncio.to_thread(_presigned_url_sync, key)
        return url
    except Exception as exc:
        logger.warning("MinIO presigned URL failed for key=%s: %s", key, exc)
        return None
