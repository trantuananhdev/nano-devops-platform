"""
Rate Limiter — sliding window per IP, lưu trạng thái trong Redis.

Không dùng slowapi (có issue với fastapi async).
Implement thuần Redis sliding window: simple, reliable, no extra deps.

Rules mặc định:
  - POST /appraise   → 5 req/60s per IP  (tốn kém nhất)
  - POST /*/upload   → 10 req/60s per IP
  - GET  default     → 120 req/60s per IP

Config qua ENV:
  RATE_LIMIT_APPRAISE=5
  RATE_LIMIT_UPLOAD=10
  RATE_LIMIT_DEFAULT=120
  RATE_LIMIT_WINDOW_SECONDS=60
  RATE_LIMIT_ENABLED=true
"""

from __future__ import annotations

import logging
import time
from typing import Any

import redis.asyncio as aioredis
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from app.core.config import get_settings
from app.core.metrics import RATE_LIMIT_HITS

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Sliding window implementation
# ---------------------------------------------------------------------------

async def _check_rate_limit(
    redis_client: aioredis.Redis,
    key: str,
    limit: int,
    window_s: int,
) -> tuple[bool, int, int]:
    """
    Sliding window rate limit check using Redis sorted set.

    Returns:
        (allowed: bool, current_count: int, reset_in_seconds: int)
    """
    now = time.time()
    window_start = now - window_s

    pipe = redis_client.pipeline()
    # Remove expired entries
    pipe.zremrangebyscore(key, 0, window_start)
    # Count current window
    pipe.zcard(key)
    # Add current request
    pipe.zadd(key, {str(now): now})
    # Set TTL
    pipe.expire(key, window_s + 1)
    results = await pipe.execute()

    current_count: int = results[1]  # count BEFORE adding new request

    allowed = current_count < limit
    reset_in = window_s  # conservative estimate

    return allowed, current_count + 1, reset_in


# ---------------------------------------------------------------------------
# Route → limit mapping
# ---------------------------------------------------------------------------

def _get_limit_for_path(path: str, method: str, settings: Any) -> tuple[int, int]:
    """Return (limit, window_seconds) for the given path + method."""
    window = settings.rate_limit_window_s

    if method == "POST" and "/appraise" in path:
        return settings.rate_limit_appraise, window
    if method == "POST" and "/upload" in path:
        return settings.rate_limit_upload, window
    # MCP tool calls are as expensive as appraise — share same limit
    if method == "POST" and path.startswith("/mcp/tools/call"):
        return settings.rate_limit_appraise, window
    return settings.rate_limit_default, window


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    """Sliding window rate limiter backed by Redis."""

    def __init__(self, app: Any, redis_url: str) -> None:
        super().__init__(app)
        self._redis_url = redis_url
        self._redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self._redis_url,
                encoding="utf-8",
                decode_responses=True,
            )
        return self._redis

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()

        if not settings.rate_limit_enabled:
            return await call_next(request)

        # Skip non-API paths and metrics endpoint
        path = request.url.path
        if (not path.startswith("/api/") and not path.startswith("/mcp")) or path == "/metrics":
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        method    = request.method
        limit, window = _get_limit_for_path(path, method, settings)

        # Redis key: rl:{ip}:{method}:{path_normalized}
        path_key = path.replace("/", "_").strip("_")
        redis_key = f"rl:{client_ip}:{method}:{path_key}"

        try:
            redis = await self._get_redis()
            allowed, count, reset_in = await _check_rate_limit(redis, redis_key, limit, window)
        except Exception as exc:
            # Redis unavailable — allow request, log warning
            logger.warning("Rate limit Redis check failed: %s — allowing request", exc)
            return await call_next(request)

        # Add rate limit headers always
        response_headers = {
            "X-RateLimit-Limit":     str(limit),
            "X-RateLimit-Remaining": str(max(0, limit - count)),
            "X-RateLimit-Reset":     str(reset_in),
        }

        if not allowed:
            RATE_LIMIT_HITS.labels(endpoint=path).inc()
            logger.warning("Rate limit exceeded: ip=%s path=%s count=%d limit=%d", client_ip, path, count, limit)
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Quá nhiều yêu cầu. Vui lòng thử lại sau.",
                    "retry_after_seconds": reset_in,
                },
                headers=response_headers,
            )

        response = await call_next(request)
        for k, v in response_headers.items():
            response.headers[k] = v
        return response
