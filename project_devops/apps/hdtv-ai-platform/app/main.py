import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.core.config import get_settings
from app.core.database import engine, async_session_factory
from app.core.metrics import get_metrics_output, HTTP_REQUESTS, HTTP_DURATION
from app.core.rate_limiter import RateLimitMiddleware
from app.core.tracing import configure_tracer, instrument_fastapi
from app.models.entities import Dossier
from app.routers import api_router
from app.routers import ws as ws_router
from app.services import search_service
import time


async def _warmup_search() -> None:
    """Index all dossiers into Meilisearch on startup (best-effort)."""
    await search_service.ensure_index()
    try:
        async with async_session_factory() as session:
            rows = (await session.execute(select(Dossier).order_by(Dossier.id))).scalars().all()
            docs = [search_service.dossier_to_doc(d) for d in rows]
        await search_service.index_all_dossiers(docs)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).warning("Search warm-up failed: %s", exc)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # NOTE: Schema creation is handled by Alembic migrations (./cli.sh hdtv-migrate).
    # create_all() is intentionally removed — running both causes race conditions
    # and silent schema drift when migration files exist.
    asyncio.create_task(_warmup_search())
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()

    # T-28: Configure OTel tracing before app construction (opt-in, default off)
    if settings.tracing_enabled:
        configure_tracer(settings.app_name)

    app = FastAPI(title=settings.app_name, lifespan=lifespan)

    origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if origins != ["*"] else ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Rate limiting middleware (before prometheus so rejected requests are counted)
    app.add_middleware(RateLimitMiddleware, redis_url=settings.redis_url)

    # Prometheus HTTP metrics middleware
    @app.middleware("http")
    async def prometheus_middleware(request: Request, call_next):
        start = time.perf_counter()
        # Normalize path to avoid label explosion (strip IDs)
        path = request.url.path
        # /api/v1/dossiers/123 → /api/v1/dossiers/{id}
        import re
        normalized = re.sub(r"/\d+", "/{id}", path)

        response = await call_next(request)

        duration = time.perf_counter() - start
        HTTP_REQUESTS.labels(
            method=request.method,
            endpoint=normalized,
            status_code=str(response.status_code),
        ).inc()
        HTTP_DURATION.labels(endpoint=normalized).observe(duration)
        return response

    # Prometheus scrape endpoint (no auth — internal only, UFW protects externally)
    @app.get("/metrics", include_in_schema=False)
    async def metrics_endpoint():
        data, content_type = get_metrics_output()
        return Response(content=data, media_type=content_type)

    app.include_router(api_router, prefix=settings.api_prefix)
    app.include_router(ws_router.router)

    # T-28: FastAPI auto-instrumentation (must be after routers are registered)
    if settings.tracing_enabled:
        instrument_fastapi(app)

    return app


app = create_app()
