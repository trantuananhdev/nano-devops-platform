from celery import Celery
from celery.schedules import crontab

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "hdtv",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
)
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Ho_Chi_Minh",
    enable_utc=True,
)

# ---------------------------------------------------------------------------
# T-27: Celery Beat — RAG ingestion pipeline schedules
# ---------------------------------------------------------------------------
celery_app.conf.beat_schedule = {
    # Ingest new legal documents every 6 hours
    "ingest-legal-documents-every-6h": {
        "task":     "ingest_legal_documents",
        "schedule": crontab(minute=0, hour="*/6"),   # 00:00, 06:00, 12:00, 18:00
        "kwargs":   {},                               # uses rag_docs_dir from config
    },
    # Clean up stale embeddings daily at 02:00 (VN time = UTC+7 → UTC 19:00 prev day)
    "cleanup-stale-embeddings-daily": {
        "task":     "cleanup_stale_embeddings",
        "schedule": crontab(minute=0, hour=2),        # 02:00 Asia/Ho_Chi_Minh
    },
}

celery_app.autodiscover_tasks(["app.workers"])
