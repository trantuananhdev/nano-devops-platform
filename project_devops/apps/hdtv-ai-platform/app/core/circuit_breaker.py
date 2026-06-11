"""
T-25: Circuit Breaker — bảo vệ LLM backends khỏi cascade failure.

States:
  CLOSED   → normal operation, failures tracked in sliding window
  OPEN     → blocked, fast-fail với status="circuit_open"
  HALF_OPEN → 1 probe request allowed, nếu thành công → CLOSED

Thread-safe via asyncio.Lock (single-event-loop per worker process).
"""

from __future__ import annotations

import asyncio
import logging
import time
from enum import Enum
from typing import Any, Awaitable, Callable, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(str, Enum):
    CLOSED    = "closed"
    OPEN      = "open"
    HALF_OPEN = "half_open"


class CircuitBreakerOpen(Exception):
    """Raised when circuit is OPEN and call is blocked."""
    def __init__(self, backend: str, cooldown_remaining_s: float) -> None:
        self.backend = backend
        self.cooldown_remaining_s = cooldown_remaining_s
        super().__init__(
            f"Circuit OPEN for '{backend}' — cooldown {cooldown_remaining_s:.1f}s remaining"
        )


class CircuitBreaker:
    """
    Async circuit breaker với sliding window failure tracking.

    Args:
        name:              Identifier cho backend (vd: "gemini", "local_llm")
        failure_threshold: Số failures trong window trước khi trip
        window_s:          Sliding window size (seconds)
        cooldown_s:        Thời gian OPEN trước khi thử HALF_OPEN
    """

    def __init__(
        self,
        name: str,
        *,
        failure_threshold: int = 5,
        window_s: int = 60,
        cooldown_s: int = 30,
    ) -> None:
        self.name              = name
        self.failure_threshold = failure_threshold
        self.window_s          = window_s
        self.cooldown_s        = cooldown_s

        self._state: CircuitState = CircuitState.CLOSED
        self._failure_times: list[float] = []   # timestamps of recent failures
        self._opened_at: float | None    = None
        self._lock = asyncio.Lock()

    # ------------------------------------------------------------------
    # Public state inspection
    # ------------------------------------------------------------------

    @property
    def state(self) -> CircuitState:
        return self._state

    @property
    def is_open(self) -> bool:
        return self._state == CircuitState.OPEN

    def failure_count_in_window(self) -> int:
        """Count failures within the sliding window."""
        cutoff = time.monotonic() - self.window_s
        return sum(1 for t in self._failure_times if t >= cutoff)

    # ------------------------------------------------------------------
    # Core call wrapper
    # ------------------------------------------------------------------

    async def call(
        self,
        fn: Callable[..., Awaitable[T]],
        *args: Any,
        **kwargs: Any,
    ) -> T:
        """Execute fn(*args, **kwargs) through the circuit breaker.

        Raises CircuitBreakerOpen if OPEN and cooldown not expired.
        """
        async with self._lock:
            await self._maybe_transition()

            if self._state == CircuitState.OPEN:
                elapsed   = time.monotonic() - (self._opened_at or 0)
                remaining = max(0.0, self.cooldown_s - elapsed)
                logger.warning(
                    "CircuitBreaker '%s' OPEN — fast-failing (%.1fs remaining)",
                    self.name, remaining,
                )
                raise CircuitBreakerOpen(self.name, remaining)

        # Execute outside lock to avoid blocking other coroutines
        try:
            result = await fn(*args, **kwargs)
            await self._on_success()
            return result
        except CircuitBreakerOpen:
            raise
        except Exception as exc:
            await self._on_failure()
            raise exc

    # ------------------------------------------------------------------
    # State transitions
    # ------------------------------------------------------------------

    async def _maybe_transition(self) -> None:
        """Check if OPEN circuit should move to HALF_OPEN."""
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            elapsed = time.monotonic() - self._opened_at
            if elapsed >= self.cooldown_s:
                logger.info(
                    "CircuitBreaker '%s': OPEN → HALF_OPEN (cooldown expired after %.1fs)",
                    self.name, elapsed,
                )
                self._state = CircuitState.HALF_OPEN

    async def _on_success(self) -> None:
        async with self._lock:
            if self._state == CircuitState.HALF_OPEN:
                logger.info(
                    "CircuitBreaker '%s': HALF_OPEN → CLOSED (probe succeeded)", self.name
                )
                self._state         = CircuitState.CLOSED
                self._failure_times = []
                self._opened_at     = None
            elif self._state == CircuitState.CLOSED:
                # Prune old failures from window on success
                cutoff = time.monotonic() - self.window_s
                self._failure_times = [t for t in self._failure_times if t >= cutoff]

    async def _on_failure(self) -> None:
        async with self._lock:
            now = time.monotonic()
            self._failure_times.append(now)

            # Prune outside window
            cutoff = now - self.window_s
            self._failure_times = [t for t in self._failure_times if t >= cutoff]

            if self._state == CircuitState.HALF_OPEN:
                # Probe failed → back to OPEN
                logger.warning(
                    "CircuitBreaker '%s': HALF_OPEN → OPEN (probe failed)", self.name
                )
                self._state     = CircuitState.OPEN
                self._opened_at = now

            elif self._state == CircuitState.CLOSED:
                failures = len(self._failure_times)
                if failures >= self.failure_threshold:
                    logger.error(
                        "CircuitBreaker '%s': CLOSED → OPEN (%d failures in %ds window)",
                        self.name, failures, self.window_s,
                    )
                    self._state     = CircuitState.OPEN
                    self._opened_at = now

    # ------------------------------------------------------------------
    # Manual control (for testing / admin override)
    # ------------------------------------------------------------------

    async def reset(self) -> None:
        """Force circuit back to CLOSED state."""
        async with self._lock:
            self._state         = CircuitState.CLOSED
            self._failure_times = []
            self._opened_at     = None
            logger.info("CircuitBreaker '%s': manually reset to CLOSED", self.name)

    def status_dict(self) -> dict[str, Any]:
        """Return current state as dict for health/admin endpoints."""
        return {
            "name":              self.name,
            "state":             self._state.value,
            "failure_threshold": self.failure_threshold,
            "window_s":          self.window_s,
            "cooldown_s":        self.cooldown_s,
            "failures_in_window": self.failure_count_in_window(),
            "opened_at":         self._opened_at,
        }
