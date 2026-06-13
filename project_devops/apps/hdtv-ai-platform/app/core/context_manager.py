"""
Context Window Manager — Token counting + priority-based eviction cho LLM calls.

Mục tiêu:
  - Tránh gửi payload vượt context limit của model (gây 400/truncation lỗi)
  - Priority-based eviction: giữ reasoning quan trọng, drop routine observations
  - FIFO là fallback — priority scoring là primary strategy

Chiến lược đếm token:
  - Không dùng tiktoken (nặng, không phù hợp Alpine image)
  - Heuristic: 1 token ≈ 4 ký tự (OpenAI estimate, đủ chính xác)

Priority levels (cao → thấp):
  CRITICAL  — system prompt, first user message (task definition)
  HIGH      — tool failures, reflection summaries, critic verdicts
  MEDIUM    — planning messages, clarification exchanges
  LOW       — routine successful tool observations
  MINIMAL   — duplicate/verbose tool output
"""

from __future__ import annotations

import logging
import re
from enum import IntEnum
from typing import Any

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CHARS_PER_TOKEN: int = 4

_MODEL_CONTEXT_LIMITS: dict[str, int] = {
    "gemma-4-2b-it":          8_192,
    "gemma-4-4b-it":          8_192,
    "gemma-4-8b-it":          8_192,
    "gemma-4-e2b-it":         8_192,
    "gemma-2b-it":            8_192,
    "gemini-2.5-flash":    1_048_576,
    "gemini-2.5-flash-lite": 1_048_576,
    "gemini-2.0-flash":      32_768,
    "gemini-1.5-flash":      32_768,
    "default":                8_192,
}

_RESPONSE_RESERVE_TOKENS: int = 1_024

# Patterns to detect high-priority content
_FAILURE_PATTERNS = re.compile(
    r"(fail|error|exception|lỗi|thất bại|không hợp lệ|không đạt|cảnh báo|warning|vượt|thiếu)",
    re.IGNORECASE,
)
_PLAN_PATTERNS = re.compile(
    r"(plan|step|tool_call|reflection|verdict|critic|revision|escalate|kế hoạch|thẩm định)",
    re.IGNORECASE,
)

# ---------------------------------------------------------------------------
# Priority enum
# ---------------------------------------------------------------------------

class MessagePriority(IntEnum):
    MINIMAL  = 0   # Verbose/duplicate, drop first
    LOW      = 1   # Routine successful observations
    MEDIUM   = 2   # Planning, clarifications
    HIGH     = 3   # Failures, reflections, critic verdicts
    CRITICAL = 4   # System prompt, task definition


# ---------------------------------------------------------------------------
# Token estimation
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // _CHARS_PER_TOKEN)


def estimate_messages_tokens(messages: list[dict[str, str]]) -> int:
    total = 0
    for msg in messages:
        total += 4  # role header overhead
        total += estimate_tokens(msg.get("content", ""))
    total += 3  # final priming tokens
    return total


def get_context_limit(model: str) -> int:
    for key, limit in _MODEL_CONTEXT_LIMITS.items():
        if key in model.lower():
            return limit
    return _MODEL_CONTEXT_LIMITS["default"]


# ---------------------------------------------------------------------------
# Priority scoring
# ---------------------------------------------------------------------------

def score_message_priority(msg: dict[str, str], index: int, total: int) -> MessagePriority:
    """Assign retention priority to a message.

    Rules (highest priority wins):
    - system role → CRITICAL
    - First user message (index 0 among non-system) → CRITICAL (task definition)
    - Content contains failure/error indicators → HIGH
    - Content contains plan/reflection keywords → HIGH
    - assistant messages near end → MEDIUM
    - Everything else → LOW
    """
    role = msg.get("role", "")
    content = msg.get("content", "")

    if role == "system":
        return MessagePriority.CRITICAL

    # First user message is the task definition — always keep
    if role == "user" and index == 0:
        return MessagePriority.CRITICAL

    # Failure indicators are highly informative
    if _FAILURE_PATTERNS.search(content):
        return MessagePriority.HIGH

    # Planning, reflection, critic content
    if _PLAN_PATTERNS.search(content):
        return MessagePriority.HIGH

    # Recent messages (last 20% of conversation) are more relevant
    recency_threshold = max(0, int(total * 0.8))
    if index >= recency_threshold:
        return MessagePriority.MEDIUM

    # Long routine observations (>500 chars) that are just data dumps → LOW
    if len(content) > 2000 and role == "assistant":
        return MessagePriority.MINIMAL

    return MessagePriority.LOW


# ---------------------------------------------------------------------------
# Truncation
# ---------------------------------------------------------------------------

def truncate_text(text: str, max_tokens: int) -> str:
    max_chars = max_tokens * _CHARS_PER_TOKEN
    if len(text) <= max_chars:
        return text
    cut_text = text[:max_chars - 30]
    logger.debug("truncate_text: cut %d chars → %d chars", len(text), len(cut_text))
    return cut_text + " … [nội dung đã cắt bớt]"


# ---------------------------------------------------------------------------
# Priority-based fit_messages
# ---------------------------------------------------------------------------

def fit_messages(
    messages: list[dict[str, str]],
    model: str = "default",
    *,
    max_tokens: int | None = None,
) -> tuple[list[dict[str, str]], int]:
    """Trim messages list to fit within model context window.

    Strategy (Priority-based, not pure FIFO):
    1. Always keep system prompt (CRITICAL).
    2. Score all non-system messages by priority.
    3. Drop lowest-priority messages first (MINIMAL → LOW → MEDIUM).
    4. Never drop HIGH or CRITICAL messages.
    5. If a message must be truncated to fit, truncate content instead of drop.

    Returns:
        (trimmed_messages, estimated_tokens_used)
    """
    limit = max_tokens or (get_context_limit(model) - _RESPONSE_RESERVE_TOKENS)

    system_msgs = [m for m in messages if m.get("role") == "system"]
    other_msgs  = [m for m in messages if m.get("role") != "system"]

    system_tokens = estimate_messages_tokens(system_msgs)
    remaining = limit - system_tokens

    if remaining <= 0:
        logger.warning(
            "fit_messages: system prompt alone uses %d tokens (limit=%d) — truncating",
            system_tokens, limit,
        )
        if system_msgs:
            trimmed_sys = dict(system_msgs[-1])
            trimmed_sys["content"] = truncate_text(trimmed_sys.get("content", ""), limit - 100)
            system_msgs = [trimmed_sys]
        return system_msgs, estimate_messages_tokens(system_msgs)

    n = len(other_msgs)

    # Score each message
    scored: list[tuple[int, MessagePriority, dict[str, str]]] = [
        (i, score_message_priority(m, i, n), m)
        for i, m in enumerate(other_msgs)
    ]

    # Sort by priority ascending (drop low priority first) while preserving order
    # Strategy: try fitting all, then drop lowest priority until budget fits
    candidates = list(scored)  # [(original_index, priority, msg)]

    # First pass: try to fit everything
    total_tokens = estimate_messages_tokens([m for _, _, m in candidates])
    dropped_count = 0

    while total_tokens > remaining and candidates:
        # Find lowest priority message (excluding CRITICAL & HIGH) to drop
        droppable = [
            (i, p, m) for i, p, m in candidates
            if p < MessagePriority.HIGH
        ]
        if not droppable:
            # All remaining are HIGH/CRITICAL — truncate the largest one instead
            largest = max(candidates, key=lambda x: estimate_tokens(x[2].get("content", "")))
            idx_in_candidates = next(
                k for k, (i, p, m) in enumerate(candidates) if i == largest[0]
            )
            original_msg = candidates[idx_in_candidates][2]
            truncated_content = truncate_text(
                original_msg.get("content", ""),
                max(100, remaining // 2),
            )
            truncated_msg = dict(original_msg)
            truncated_msg["content"] = truncated_content
            candidates[idx_in_candidates] = (
                candidates[idx_in_candidates][0],
                candidates[idx_in_candidates][1],
                truncated_msg,
            )
            total_tokens = estimate_messages_tokens([m for _, _, m in candidates])
            break

        # Drop the lowest-priority, then oldest among ties
        droppable.sort(key=lambda x: (x[1], -x[0]))  # lowest priority, oldest first
        to_drop = droppable[0]
        candidates = [(i, p, m) for i, p, m in candidates if i != to_drop[0]]
        dropped_count += 1
        total_tokens = estimate_messages_tokens([m for _, _, m in candidates])

    if dropped_count > 0:
        logger.info(
            "fit_messages: dropped %d message(s) by priority (model=%s, limit=%d)",
            dropped_count, model, limit,
        )
        try:
            from app.core.metrics import CONTEXT_TRUNCATIONS
            CONTEXT_TRUNCATIONS.labels(model=model).inc()
        except Exception:
            pass

    # Restore original order
    candidates.sort(key=lambda x: x[0])
    final_messages = system_msgs + [m for _, _, m in candidates]
    total_used = estimate_messages_tokens(final_messages)

    return final_messages, total_used


# ---------------------------------------------------------------------------
# Observations FIFO buffer (for agent loop)
# ---------------------------------------------------------------------------

def trim_observations(
    observations: list[str],
    max_tokens: int = 2_048,
) -> list[str]:
    """Keep the most recent observations that fit within max_tokens total.

    Failure observations are kept preferentially over successes.
    """
    if not observations:
        return []

    # Separate failures (keep preferentially) from successes
    failures = [(i, obs) for i, obs in enumerate(observations) if _FAILURE_PATTERNS.search(obs)]
    successes = [(i, obs) for i, obs in enumerate(observations) if not _FAILURE_PATTERNS.search(obs)]

    kept_indexed: list[tuple[int, str]] = []
    budget = max_tokens

    # Allocate failures first (prioritized)
    failure_budget = int(budget * 0.6)  # up to 60% for failures
    for i, obs in reversed(failures):
        cost = estimate_tokens(obs)
        if cost <= failure_budget:
            kept_indexed.append((i, obs))
            failure_budget -= cost
            budget -= cost

    # Fill remainder with most recent successes
    for i, obs in reversed(successes):
        cost = estimate_tokens(obs)
        if cost <= budget - failure_budget:
            kept_indexed.append((i, obs))
            budget -= cost

    # Sort back to original order
    kept_indexed.sort(key=lambda x: x[0])
    kept = [obs for _, obs in kept_indexed]

    dropped = len(observations) - len(kept)
    if dropped > 0:
        logger.debug("trim_observations: kept %d/%d (priority-weighted)", len(kept), len(observations))
    return kept
