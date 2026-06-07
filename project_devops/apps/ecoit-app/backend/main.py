"""
EcoIT App — FastAPI Backend
Hello World build — test CI/CD pipeline end-to-end.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from core.config import settings
from api.v1.router import router as v1_router

log = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    log.info("startup", app=settings.APP_NAME, env=settings.APP_ENV)
    # DB & Redis init — enabled when services are available
    # Gracefully skip if not configured (hello world mode)
    try:
        from core.database import init_db
        await init_db()
        log.info("db.connected")
    except Exception as e:
        log.warning("db.skipped", reason=str(e))

    try:
        from core.redis import init_redis
        await init_redis()
        log.info("redis.connected")
    except Exception as e:
        log.warning("redis.skipped", reason=str(e))

    yield

    try:
        from core.database import close_db
        await close_db()
    except Exception:
        pass
    try:
        from core.redis import close_redis
        await close_redis()
    except Exception:
        pass

    log.info("shutdown", app=settings.APP_NAME)


app = FastAPI(
    title=f"{settings.APP_NAME} API",
    description="EcoIT Trial — Hello World Test Build",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Mở rộng cho dev test — thu hẹp lại khi production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["ops"])
async def health() -> JSONResponse:
    """Health check — bắt buộc có cho Ansible + Docker."""
    return JSONResponse({
        "status": "ok",
        "app": settings.APP_NAME,
        "env": settings.APP_ENV,
        "version": "0.1.0",
    })


app.include_router(v1_router, prefix="/api/v1")
