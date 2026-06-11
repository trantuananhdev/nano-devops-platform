"""
LLM client — thin compatibility shim (legacy entry point).

## Architecture note
All LLM calls now go through `llm_router.llm_call(AgentRole, messages)`, which
provides: circuit breaker (T-25), Gemini ↔ local fallback, per-role audit labels,
key rotation (T-33), and context window management (T-27/T-40).

`chat_completions()` exists solely for backward compatibility with external callers
that haven't been migrated.  New code MUST use llm_router directly.

## Migration guide
```python
# ❌ Old (bypasses circuit breaker label — routes as AgentRole.EXECUTOR)
from app.services.llm_client import chat_completions
result = await chat_completions(messages, response_format_json=True)

# ✅ New (full router path — correct role label on FE dashboard)
from app.services.llm_router import AgentRole, llm_call
result = await llm_call(AgentRole.PLANNER, messages, response_format_json=True)
```

## Ignored parameters (API compat stubs)
- `model`: router selects model from role config; caller-provided value is ignored.
- `max_retries`: router owns retry/circuit logic; caller-provided value is ignored.
"""

import logging
from typing import Any

from app.services.llm_router import AgentRole, llm_call

logger = logging.getLogger(__name__)


async def chat_completions(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,           # API compat stub — ignored, router decides
    temperature: float = 0.2,
    response_format_json: bool = False,
    max_retries: int = 2,               # API compat stub — ignored, router owns retries
) -> str:
    """Delegate to llm_router using AgentRole.EXECUTOR (legacy default role).

    Prefer ``llm_router.llm_call(AgentRole.X, messages)`` for new code so the
    correct role label appears on the Agent Intelligence dashboard (T-24).
    """
    if model is not None:
        logger.debug(
            "chat_completions: 'model=%s' ignored — router selects model from role config", model
        )
    if max_retries != 2:  # 2 is the default; non-default indicates caller expectation
        logger.debug(
            "chat_completions: 'max_retries=%d' ignored — router owns retry/circuit logic",
            max_retries,
        )

    return await llm_call(
        AgentRole.EXECUTOR,
        messages,
        response_format_json=response_format_json,
        temperature=temperature,
    )
