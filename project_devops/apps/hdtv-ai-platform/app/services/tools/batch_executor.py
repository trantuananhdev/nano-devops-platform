"""
T-18 + T-30: Parallel tool execution via asyncio.gather with retry support.

T-30 additions:
  - max_retries parameter: retry TRANSIENT errors once with backoff
  - retried flag in result for audit correlation
  - per-tool retry metrics via TOOL_RETRIES counter
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from app.core.config import get_settings
from app.core.metrics import TOOL_RETRIES
from app.services.tools.base import ToolErrorType, execute_tool

logger = logging.getLogger(__name__)


async def _run_one_with_retry(
    tool_name: str,
    tool_input: dict[str, Any],
    *,
    max_retries: int,
    retry_backoff_s: float,
) -> tuple[str, dict[str, Any], int, bool]:
    """Execute one tool with optional retry on TRANSIENT errors.

    Args:
        tool_name:       Tool to call
        tool_input:      Input parameters
        max_retries:     How many times to retry on TRANSIENT error (0 = no retry)
        retry_backoff_s: Seconds to wait between retries

    Returns:
        (tool_name, output, elapsed_ms, retried)
        retried=True means at least one retry was attempted.
    """
    retried = False
    attempts = 0
    last_output: dict[str, Any] = {}
    last_elapsed: int = 0

    while True:
        output, elapsed_ms = await execute_tool(tool_name, tool_input)
        attempts += 1
        last_output = output
        last_elapsed = elapsed_ms

        error_type = output.get("error_type")

        # Success or non-retryable error → return immediately
        if "error" not in output:
            return tool_name, output, elapsed_ms, retried

        if error_type == ToolErrorType.BAD_INPUT or error_type == ToolErrorType.UNAVAILABLE:
            # These cannot be fixed by retrying with the same input
            logger.debug(
                "Tool %s: error_type=%s — no retry (fix input or use fallback)",
                tool_name, error_type,
            )
            return tool_name, output, elapsed_ms, retried

        # TRANSIENT or UNKNOWN: retry if budget available
        if attempts > max_retries:
            last_output = {**output, "retried": retried}
            return tool_name, last_output, last_elapsed, retried

        retried = True
        TOOL_RETRIES.labels(tool_name=tool_name, error_type=str(error_type)).inc()
        logger.warning(
            "Tool %s error (attempt %d/%d, error_type=%s) — retrying in %.1fs",
            tool_name, attempts, max_retries + 1, error_type, retry_backoff_s,
        )
        await asyncio.sleep(retry_backoff_s)


async def execute_parallel(
    tool_calls: list[dict[str, Any]],
    *,
    max_retries: int | None = None,
    retry_backoff_s: float | None = None,
) -> tuple[list[tuple[str, dict[str, Any], int]], int]:
    """Execute multiple tools concurrently, with per-tool retry on transient errors.

    Args:
        tool_calls:      List of {"tool_name": str, "tool_input": dict}
        max_retries:     Retry budget per tool (None = use config default)
        retry_backoff_s: Seconds between retries (None = use config default)

    Returns:
        (results, wall_ms) where results is list of (tool_name, output, elapsed_ms).
        Preserves input order (asyncio.gather guarantee).
    """
    if not tool_calls:
        return [], 0

    cfg = get_settings()
    _max_retries     = max_retries     if max_retries     is not None else cfg.tool_max_retries
    _retry_backoff_s = retry_backoff_s if retry_backoff_s is not None else cfg.tool_retry_backoff_s

    wall_start = time.perf_counter()
    raw_results = await asyncio.gather(
        *[
            _run_one_with_retry(
                tc["tool_name"],
                tc["tool_input"],
                max_retries=_max_retries,
                retry_backoff_s=_retry_backoff_s,
            )
            for tc in tool_calls
        ]
    )
    wall_ms = int((time.perf_counter() - wall_start) * 1000)

    # Strip retried flag from final tuple (kept in output dict as 'retried' key)
    results = [(name, output, elapsed) for name, output, elapsed, _retried in raw_results]

    retried_count = sum(1 for _, _, _, r in raw_results if r)
    logger.info(
        "Parallel batch: %d tools, %dms wall time, sum=%dms%s",
        len(tool_calls),
        wall_ms,
        sum(r[2] for r in results),
        f", retried={retried_count}" if retried_count else "",
    )
    return results, wall_ms
