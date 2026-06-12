"""
Context Window Manager — Token counting + truncation cho LLM calls.

Mục tiêu:
  - Tránh gửi payload vượt context limit của model lên LLM API (gây 400/truncation lỗi)
  - FIFO rotation tin nhắn cũ (giữ system prompt + N tin nhắn cuối)
  - Trả về số token ước tính đã dùng để Prometheus tracking

Chiến lược đếm token:
  - Không dùng tiktoken (nặng, không phù hợp Alpine image)
  - Dùng heuristic: 1 token ≈ 4 ký tự (chuẩn OpenAI estimate)
  - Đủ chính xác cho purpose bảo vệ context limit
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Ký tự trên mỗi token (heuristic — OpenAI: ~4 chars/token)
_CHARS_PER_TOKEN: int = 4

# Context limits per model (tokens)
_MODEL_CONTEXT_LIMITS: dict[str, int] = {
    "gemma-4-2b-it":         8_192,
    "gemma-4-4b-it":         8_192,
    "gemma-4-8b-it":         8_192,
    "gemma-4-e2b-it":        8_192,   # Gemma 4 E2B (2B params, 8K context)
    "gemma-2b-it":          8_192,   # Gemma 2B (2B params, 8K context)
    "gemini-2.5-flash":    1_048_576,   # 1M token context window
    "gemini-2.5-flash-lite": 1_048_576,
    "gemini-2.0-flash":      32_768,
    "gemini-1.5-flash":      32_768,
    "default":              8_192,
}

# Dự trữ token cho response của model (output buffer)
_RESPONSE_RESERVE_TOKENS: int = 1_024

# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    """Estimate token count from raw text using char-based heuristic."""
    if not text:
        return 0
    return max(1, len(text) // _CHARS_PER_TOKEN)


def estimate_messages_tokens(messages: list[dict[str, str]]) -> int:
    """Estimate total tokens for an OpenAI-style messages list."""
    total = 0
    for msg in messages:
        # Role header overhead (~4 tokens per message)
        total += 4
        total += estimate_tokens(msg.get("content", ""))
    # Final priming tokens (~3)
    total += 3
    return total


def get_context_limit(model: str) -> int:
    """Return the context limit in tokens for the given model name."""
    for key, limit in _MODEL_CONTEXT_LIMITS.items():
        if key in model.lower():
            return limit
    return _MODEL_CONTEXT_LIMITS["default"]


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------

def truncate_text(text: str, max_tokens: int) -> str:
    """Truncate text to fit within max_tokens (appends marker if cut)."""
    max_chars = max_tokens * _CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text
    cut_text = text[:max_chars - 30]
    logger.debug("truncate_text: cut %d chars → %d chars", len(text), len(cut_text))
    return cut_text + " … [nội dung đã cắt bớt]"


def fit_messages(
    messages: list[dict[str, str]],
    model: str = "default",
    *,
    max_tokens: int | None = None,
) -> tuple[list[dict[str, str]], int]:
    """
    Trim messages list to fit within model context window.

    Strategy (FIFO — keep recent):
    1. Always keep system prompt (role=system)
    2. Keep as many recent user/assistant messages as fit
    3. If a single message body exceeds budget, truncate its content

    Returns:
        (trimmed_messages, estimated_tokens_used)
    """
    limit = max_tokens or (get_context_limit(model) - _RESPONSE_RESERVE_TOKENS)

    # Separate system + non-system
    system_msgs = [m for m in messages if m.get("role") == "system"]
    other_msgs  = [m for m in messages if m.get("role") != "system"]

    # Token cost of system messages (must keep all)
    system_tokens = estimate_messages_tokens(system_msgs)
    remaining = limit - system_tokens

    if remaining <= 0:
        # Edge case: system prompt alone exceeds limit — truncate last system msg
        logger.warning(
            "fit_messages: system prompt alone uses %d tokens (limit=%d) — truncating",
            system_tokens, limit,
        )
        if system_msgs:
            trimmed_sys = dict(system_msgs[-1])
            trimmed_sys["content"] = truncate_text(trimmed_sys.get("content", ""), limit - 100)
            system_msgs = [trimmed_sys]
        return system_msgs, estimate_messages_tokens(system_msgs)

    # Fill from newest → oldest (FIFO: keep recent)
    kept: list[dict[str, str]] = []
    for msg in reversed(other_msgs):
        msg_tokens = estimate_messages_tokens([msg])
        if msg_tokens <= remaining:
            kept.insert(0, msg)
            remaining -= msg_tokens
        else:
            # Try to fit a truncated version of this message
            truncated = dict(msg)
            truncated["content"] = truncate_text(msg.get("content", ""), remaining - 8)
            truncated_tokens = estimate_messages_tokens([truncated])
            if truncated_tokens < remaining and truncated["content"]:
                kept.insert(0, truncated)
                remaining -= truncated_tokens
                logger.debug("fit_messages: truncated one message to fit context")
            else:
                logger.debug(
                    "fit_messages: dropped %s message (too large, %d tokens remaining)",
                    msg.get("role"), remaining,
                )
            break  # Stop after first drop — older messages also dropped

    final_messages = system_msgs + kept
    total_tokens   = estimate_messages_tokens(final_messages)

    dropped = len(other_msgs) - len(kept)
    if dropped > 0:
        logger.info(
            "fit_messages: dropped %d old message(s) to fit context limit=%d (model=%s)",
            dropped, limit, model,
        )
        # T-27: Emit Prometheus metric when context is trimmed
        try:
            from app.core.metrics import CONTEXT_TRUNCATIONS
            CONTEXT_TRUNCATIONS.labels(model=model).inc()
        except Exception:
            pass  # Never block fit_messages on metrics failure

    return final_messages, total_tokens


# ---------------------------------------------------------------------------
# Observations FIFO buffer (for agent loop)
# ---------------------------------------------------------------------------

def trim_observations(
    observations: list[str],
    max_tokens: int = 2_048,
) -> list[str]:
    """Keep the most recent observations that fit within max_tokens total.

    Used by react_agent to prevent unbounded observation growth.
    """
    if not observations:
        return []

    kept: list[str] = []
    budget = max_tokens
    for obs in reversed(observations):
        cost = estimate_tokens(obs)
        if cost <= budget:
            kept.insert(0, obs)
            budget -= cost
        else:
            break  # Oldest observations dropped

    dropped = len(observations) - len(kept)
    if dropped > 0:
        logger.debug("trim_observations: dropped %d old observation(s)", dropped)
    return kept
