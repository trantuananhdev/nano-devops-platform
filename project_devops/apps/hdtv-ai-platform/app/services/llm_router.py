"""
LLM Router — Multi-model dispatch cho HDTV AI Platform.

Chiến lược:
  - Ubuntu llama-server (Gemma 4): heavy reasoning tasks — planner, reflector, summary
  - Gemini Flash (mock): specialist agents — legal, financial, ocr, critic
    (các task này cần domain knowledge + JSON format chính xác hơn model nhỏ local)

Mỗi role được gán nhãn rõ ràng trong AiAuditLog.  Khi có model endpoint thực
chỉ cần đổi ROLE_BACKENDS[role]["backend"] = "local" mà không cần đổi code.

Usage:
    from app.services.llm_router import llm_call, AgentRole

    result = await llm_call(AgentRole.PLANNER, messages, response_format_json=True)
"""

from __future__ import annotations

import asyncio
import contextvars
import json
import logging
import threading
import time
from enum import Enum
from typing import TYPE_CHECKING, Any

import httpx

from app.core.config import get_settings
from app.core.context_manager import fit_messages, trim_observations  # noqa: F401 (re-export)
from app.core.circuit_breaker import CircuitBreaker, CircuitBreakerOpen
from app.core.metrics import (
    CONTEXT_TRUNCATIONS,
    LLM_CALLS,
    LLM_TOKENS,
    LLM_CIRCUIT_TRIPS,
)

if TYPE_CHECKING:
    from app.core.config import Settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# ContextVar for token capture — set by llm_call(), written by _call_* fns.
# Pattern: contextvar flows down through circuit breaker without changing sigs.
# ---------------------------------------------------------------------------
_token_capture: contextvars.ContextVar[dict[str, Any] | None] = contextvars.ContextVar(
    "_token_capture", default=None
)

# ---------------------------------------------------------------------------
# Agent roles — mỗi role = 1 "model" riêng trên FE dashboard
# ---------------------------------------------------------------------------

class AgentRole(str, Enum):
    PLANNER    = "planner"      # Lập kế hoạch thực thi
    EXECUTOR   = "executor"     # Điều phối tool calls (dùng Ubuntu)
    LEGAL      = "legal"        # Chuyên gia pháp lý
    FINANCIAL  = "financial"    # Chuyên gia tài chính ERP
    OCR        = "ocr"          # Trích xuất văn bản
    REFLECTOR  = "reflector"    # Phản tư kết quả
    CRITIC     = "critic"       # Kiểm duyệt bản thảo
    SUMMARY    = "summary"      # Tổng hợp báo cáo
    TOOL_MOCK  = "tool_mock"    # Generic tool simulation


# ---------------------------------------------------------------------------
# Backend configs — "local" = Ubuntu llama-server, "gemini" = Gemini Flash API
# ---------------------------------------------------------------------------

_ROLE_CONFIG: dict[str, dict[str, Any]] = {
    AgentRole.PLANNER: {
        "backend":     "local",            # Ubuntu Gemma 4 — đủ tốt cho planning JSON
        "label":       "Gemma-4-Planner",
        "temperature": 0.2,
        "json_mode":   True,
        "description": "Lập kế hoạch thực thi thẩm định (Ubuntu llama-server)",
    },
    AgentRole.EXECUTOR: {
        "backend":     "local",
        "label":       "Gemma-4-Executor",
        "temperature": 0.1,
        "json_mode":   True,
        "description": "Điều phối ReAct loop (Ubuntu llama-server)",
    },
    AgentRole.LEGAL: {
        "backend":     "gemini",
        "label":       "Gemini-2.5-Flash-Legal",
        "temperature": 0.1,
        "json_mode":   True,
        "description": "Chuyên gia pháp lý EVN (Gemini 2.5 Flash)",
    },
    AgentRole.FINANCIAL: {
        "backend":     "gemini",
        "label":       "Gemini-2.5-Flash-Financial",
        "temperature": 0.1,
        "json_mode":   True,
        "description": "Chuyên gia tài chính ERP (Gemini 2.5 Flash)",
    },
    AgentRole.OCR: {
        "backend":     "gemini",
        "label":       "Gemini-2.5-Flash-OCR",
        "temperature": 0.1,
        "json_mode":   True,
        "description": "Trích xuất OCR từ hồ sơ PDF (Gemini 2.5 Flash)",
    },
    AgentRole.REFLECTOR: {
        "backend":     "local",            # Gemma 4 — reflection + JSON verdict
        "label":       "Gemma-4-Reflector",
        "temperature": 0.2,
        "json_mode":   True,
        "description": "Phản tư kết quả thực thi (Ubuntu llama-server)",
    },
    AgentRole.CRITIC: {
        "backend":     "gemini",
        "label":       "Gemini-2.5-Flash-Critic",
        "temperature": 0.15,
        "json_mode":   True,
        "description": "Kiểm duyệt bản thảo báo cáo (Gemini 2.5 Flash)",
    },
    AgentRole.SUMMARY: {
        "backend":     "local",            # Ubuntu — free-form Vietnamese text
        "label":       "Gemma-4-Reporter",
        "temperature": 0.3,
        "json_mode":   False,
        "description": "Tổng hợp báo cáo thẩm định (Ubuntu llama-server)",
    },
    AgentRole.TOOL_MOCK: {
        "backend":     "gemini",
        "label":       "Gemini-2.5-Flash-ToolSim",
        "temperature": 0.2,
        "json_mode":   True,
        "description": "Giả lập phản hồi tool ERP/DOffice/PMIS (Gemini 2.5 Flash)",
    },
}


# ---------------------------------------------------------------------------
# Gemini async client (ported from geminiProvider.py, fully async)
# ---------------------------------------------------------------------------

_key_index = 0
_key_lock  = threading.Lock()
# Per-key cooldown tracking: key → timestamp when it went into cooldown
_key_cooldown: dict[str, float] = {}
_key_cooldown_s: int = 60  # Cooldown duration for a key after 429/403


def _next_gemini_key(keys: list[str]) -> str:
    """Round-robin key rotation, skipping keys currently in cooldown."""
    global _key_index
    now = time.monotonic()
    with _key_lock:
        # Try up to len(keys) times to find a non-cooldown key
        for _ in range(len(keys)):
            key = keys[_key_index % len(keys)]
            _key_index += 1
            cooldown_until = _key_cooldown.get(key, 0)
            if now >= cooldown_until:
                return key
        # All keys in cooldown — return the one whose cooldown expires soonest
        best = min(keys, key=lambda k: _key_cooldown.get(k, 0))
        return best


def _mark_key_cooldown(key: str) -> None:
    """Put a key into cooldown after 429/403."""
    with _key_lock:
        _key_cooldown[key] = time.monotonic() + _key_cooldown_s
        logger.warning("Gemini key cooldown set (%.0fs): %s…", _key_cooldown_s, key[:12])


def _build_gemini_body(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    json_mode: bool = False,
    max_tokens: int = 4096,
) -> dict[str, Any]:
    """Convert OpenAI-style messages to Gemini generateContent body."""
    system_msg = next((m for m in messages if m.get("role") == "system"), None)
    user_msgs  = [m for m in messages if m.get("role") != "system"]

    prompt = ""
    if system_msg:
        prompt += f"[INSTRUCTION]\n{system_msg['content']}\n\n"
    prompt += "\n\n".join(m.get("content", "") for m in user_msgs)

    gen_config: dict[str, Any] = {
        "temperature":    temperature,
        "maxOutputTokens": max_tokens,
    }
    if json_mode:
        gen_config["responseMimeType"] = "application/json"

    return {
        "contents":         [{"parts": [{"text": prompt}]}],
        "generationConfig": gen_config,
    }


# ---------------------------------------------------------------------------
# T-25: Circuit Breaker instances — one per backend
# ---------------------------------------------------------------------------

def _get_cb_gemini() -> CircuitBreaker:
    """Lazy-init Gemini circuit breaker using settings."""
    if not hasattr(_get_cb_gemini, "_instance"):
        cfg = get_settings()
        _get_cb_gemini._instance = CircuitBreaker(  # type: ignore[attr-defined]
            "gemini",
            failure_threshold=cfg.llm_circuit_failure_threshold,
            window_s=cfg.llm_circuit_window_s,
            cooldown_s=cfg.llm_circuit_cooldown_s,
        )
    return _get_cb_gemini._instance  # type: ignore[attr-defined]


def _get_cb_local() -> CircuitBreaker:
    """Lazy-init local LLM circuit breaker using settings."""
    if not hasattr(_get_cb_local, "_instance"):
        cfg = get_settings()
        _get_cb_local._instance = CircuitBreaker(  # type: ignore[attr-defined]
            "local_llm",
            failure_threshold=cfg.llm_circuit_failure_threshold,
            window_s=cfg.llm_circuit_window_s,
            cooldown_s=cfg.llm_circuit_cooldown_s,
        )
    return _get_cb_local._instance  # type: ignore[attr-defined]


_gemini_key_cache: dict[str, Any] = {"keys": [], "cached_at": 0.0}
_gemini_key_cache_lock = asyncio.Lock()


async def _get_gemini_keys_with_db_fallback(cfg: "Settings") -> list[str]:
    """Retrieve active Gemini API keys.

    Priority:
    1. Active keys in `api_keys` table where key_type='gemini' (T-33)
    2. .env keys (GEMINI_API_KEY, GEMINI_API_KEY_1..9) as fallback

    Caches DB result for 60s behind an asyncio.Lock to prevent concurrent
    cache-miss stampedes. Cache is process-local (acceptable for single-worker
    deployment; a Redis-backed cache would be needed for multi-process).
    """
    now = time.monotonic()

    async with _gemini_key_cache_lock:
        if _gemini_key_cache["keys"] and (now - _gemini_key_cache["cached_at"]) < 60.0:
            return _gemini_key_cache["keys"]

        # Try DB
        db_keys: list[str] = []
        try:
            from app.core.database import async_session_factory
            from app.models.entities import ApiKeyType
            from app.services.api_key_service import get_active_keys_by_type

            async with async_session_factory() as db:
                db_keys = await get_active_keys_by_type(db, ApiKeyType.gemini)
        except Exception as exc:
            logger.debug("DB key fetch skipped (DB may not be ready): %s", exc)

        keys = db_keys if db_keys else cfg.gemini_api_keys
        _gemini_key_cache["keys"] = keys
        _gemini_key_cache["cached_at"] = now
        return keys


async def _call_gemini(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    json_mode:   bool  = False,
    role:        str   = "tool_mock",
) -> str:
    """Async Gemini REST call — single attempt, no internal retry loop.

    IMPORTANT: Retry/backoff is intentionally removed here.
    The circuit breaker in llm_call() wraps this function; keeping retries
    inside would cause failures to register only after N attempts rather than
    immediately, making the circuit breaker trip much later than intended.

    Key rotation and 429/403 cooldown still happen per-attempt, but each
    failure propagates up immediately so the circuit breaker can count it.

    T-33: Keys are sourced from DB first (api_keys table), falling back to .env
    when no active DB keys exist for the gemini type.
    """
    cfg = get_settings()

    # T-33: Try DB keys first, fall back to .env
    keys = await _get_gemini_keys_with_db_fallback(cfg)
    if not keys:
        raise RuntimeError("No valid Gemini API keys available (DB or .env)")

    # Context window management for Gemini
    fitted, token_est = fit_messages(messages, model=cfg.gemini_model)
    LLM_TOKENS.labels(role=role, backend="gemini").inc(token_est)

    body = _build_gemini_body(
        fitted,
        temperature=temperature,
        json_mode=json_mode,
        max_tokens=cfg.gemini_max_tokens,   # reads GEMINI_MAX_TOKENS from env
    )
    model_name = cfg.gemini_model

    api_key = _next_gemini_key(keys)
    url = (
        f"https://generativelanguage.googleapis.com/{cfg.gemini_api_version}"
        f"/models/{model_name}:generateContent?key={api_key}"
    )

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:  # 2.5 Flash cần timeout dài hơn
            resp = await client.post(
                url,
                json=body,
                headers={"Content-Type": "application/json"},
            )
            if resp.status_code in (429, 403):
                _mark_key_cooldown(api_key)
                logger.warning("Gemini HTTP %d — key cooled, propagating to circuit breaker", resp.status_code)

            if resp.status_code == 200:
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                if not text:
                    raise ValueError(f"Gemini empty response: {data}")
                LLM_CALLS.labels(role=role, backend="gemini", status="ok").inc()
                # Capture actual token counts from Gemini usageMetadata
                _cap = _token_capture.get()
                if _cap is not None:
                    meta = data.get("usageMetadata", {})
                    _cap["prompt_tokens"] = meta.get("promptTokenCount", 0)
                    _cap["completion_tokens"] = meta.get("candidatesTokenCount", 0)
                    _cap["total_tokens"] = meta.get("totalTokenCount", 0)
                    _cap["model"] = model_name
                return text

            resp.raise_for_status()

    except Exception:
        LLM_CALLS.labels(role=role, backend="gemini", status="error").inc()
        raise

    # Should not reach — raise_for_status() above covers non-200
    LLM_CALLS.labels(role=role, backend="gemini", status="error").inc()
    raise RuntimeError(f"Gemini unexpected non-200 response from {url}")


# ---------------------------------------------------------------------------
# Ubuntu llama-server (OpenAI-compatible) — async
# ---------------------------------------------------------------------------

_LLM_FALLBACK = json.dumps({
    "thought": "LLM unavailable, proceeding with rule-based checks",
    "action":  "finish",
    "tool_name":  None,
    "tool_input": {},
})


async def _call_local_llm(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    json_mode:   bool  = False,
    max_retries: int   = 2,
    role:        str   = "executor",
) -> str:
    """Call Ubuntu llama-server via OpenAI-compatible /chat/completions."""
    cfg = get_settings()

    # Context window management — trim before sending
    fitted, token_est = fit_messages(messages, model=cfg.llm_model)
    if len(fitted) < len(messages):
        # Note: CONTEXT_TRUNCATIONS already emitted inside fit_messages() (T-27)
        pass
    LLM_TOKENS.labels(role=role, backend="local").inc(token_est)

    payload: dict[str, Any] = {
        "model":       cfg.llm_model,
        "messages":    fitted,
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    url       = f"{cfg.llm_base_url.rstrip('/')}/chat/completions"
    last_exc: Exception | None = None

    async with httpx.AsyncClient(timeout=cfg.llm_timeout) as client:
        for attempt in range(1, max_retries + 2):
            try:
                resp = await client.post(url, json=payload)
                resp.raise_for_status()
                rdata = resp.json()
                LLM_CALLS.labels(role=role, backend="local", status="ok").inc()
                # Capture actual token counts from llama.cpp OpenAI-compatible usage
                _cap = _token_capture.get()
                if _cap is not None:
                    usage = rdata.get("usage", {})
                    _cap["prompt_tokens"] = usage.get("prompt_tokens", 0)
                    _cap["completion_tokens"] = usage.get("completion_tokens", 0)
                    _cap["total_tokens"] = usage.get("total_tokens", 0)
                    _cap["model"] = rdata.get("model", cfg.llm_model)
                return rdata["choices"][0]["message"]["content"]
            except (httpx.TransportError, httpx.TimeoutException) as exc:
                last_exc = exc
                if attempt <= max_retries:
                    logger.warning(
                        "Local LLM transient error (attempt %d/%d): %s — retrying",
                        attempt, max_retries + 1, exc,
                    )
                continue
            except Exception as exc:
                last_exc = exc
                break

    LLM_CALLS.labels(role=role, backend="local", status="fallback").inc()
    logger.warning(
        "Local LLM failed after %d attempts (%s) — using structured fallback",
        max_retries + 1, last_exc,
    )
    return _LLM_FALLBACK


# ---------------------------------------------------------------------------
# Public router
# ---------------------------------------------------------------------------

async def _call_gemini_with_retry(
    messages: list[dict[str, str]],
    *,
    temperature: float,
    json_mode:   bool,
    role:        str,
    max_retries: int   = 3,
    backoff_s:   float = 2.0,
) -> str:
    """Retry wrapper around _call_gemini that respects the circuit breaker.

    Each individual attempt goes through the circuit breaker so that every
    failure is counted immediately — the circuit trips after `failure_threshold`
    raw failures, not after `failure_threshold` ×  max_retries.

    Retries only on transient errors (network/timeout/429/503).
    Non-transient errors (400 bad request, auth) propagate immediately.
    """
    cfg = get_settings()
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            return await _get_cb_gemini().call(
                _call_gemini, messages, temperature=temperature, json_mode=json_mode, role=role
            )
        except CircuitBreakerOpen:
            raise  # Circuit is OPEN — propagate immediately, no point retrying
        except httpx.HTTPStatusError as exc:
            last_exc = exc
            # Do not retry on client errors other than 429/503
            if exc.response.status_code not in (429, 503) or attempt >= max_retries:
                raise
            wait = backoff_s * attempt
            logger.warning(
                "Gemini HTTP %d (attempt %d/%d) — retry in %.1fs",
                exc.response.status_code, attempt, max_retries, wait,
            )
            await asyncio.sleep(wait)
        except (httpx.TransportError, httpx.TimeoutException) as exc:
            last_exc = exc
            if attempt >= max_retries:
                raise
            wait = backoff_s * attempt
            logger.warning(
                "Gemini transient error (attempt %d/%d): %s — retry in %.1fs",
                attempt, max_retries, exc, wait,
            )
            await asyncio.sleep(wait)
        except Exception:
            raise  # Unexpected — propagate immediately

    raise RuntimeError(f"Gemini failed after {max_retries} attempts: {last_exc}")


async def llm_call(
    role:     AgentRole | str,
    messages: list[dict[str, str]],
    *,
    response_format_json: bool | None = None,
    temperature:          float | None = None,
    dossier_id:           int | None = None,
    session_id:           str | None = None,
) -> str:
    """Route an LLM call to the correct backend based on agent role.

    Args:
        role:                 AgentRole enum (or string matching AgentRole value)
        messages:             OpenAI-style messages list
        response_format_json: override JSON mode (None = use role default)
        temperature:          override temperature (None = use role default)
        dossier_id:           optional dossier context for token usage tracking
        session_id:           optional agent session ID for grouping

    Returns:
        Raw text string from whichever backend was selected.
    """
    role_str = role.value if isinstance(role, AgentRole) else str(role)
    cfg_entry = _ROLE_CONFIG.get(role_str, _ROLE_CONFIG[AgentRole.TOOL_MOCK])
    cfg = get_settings()
    _t_start = time.perf_counter()

    backend = cfg_entry["backend"]
    temp    = temperature if temperature is not None else cfg_entry["temperature"]
    jmode   = response_format_json if response_format_json is not None else cfg_entry["json_mode"]
    label   = cfg_entry["label"]

    logger.debug("llm_call role=%s backend=%s label=%s json=%s", role_str, backend, label, jmode)

    # Set token capture context — written by _call_gemini / _call_local_llm on success
    _capture: dict[str, Any] = {"backend": backend, "role": role_str, "model": label}
    _ctx_token = _token_capture.set(_capture)

    try:
        result = await _llm_call_inner(
            role_str, messages, backend=backend, temp=temp, jmode=jmode,
            cfg=cfg, cfg_entry=cfg_entry,
        )
    finally:
        # Always reset the contextvar regardless of success/failure
        _token_capture.reset(_ctx_token)

    # Fire-and-forget persist — only on success (result is bound here)
    if _capture.get("total_tokens", 0) > 0:
        duration_ms = int((time.perf_counter() - _t_start) * 1000)
        asyncio.create_task(
            _persist_token_usage(
                role=role_str,
                backend=_capture["backend"],
                model=_capture.get("model", label),
                prompt_tokens=_capture.get("prompt_tokens", 0),
                completion_tokens=_capture.get("completion_tokens", 0),
                total_tokens=_capture["total_tokens"],
                duration_ms=duration_ms,
                dossier_id=dossier_id,
                session_id=session_id,
            ),
            name=f"token_persist_{role_str}",
        )
    return result


async def _llm_call_inner(
    role_str: str,
    messages: list[dict[str, str]],
    *,
    backend: str,
    temp: float,
    jmode: bool,
    cfg: Any,
    cfg_entry: dict[str, Any],
) -> str:
    """Inner dispatch — extracted to keep llm_call() clean."""
    if backend == "local":
        try:
            return await _get_cb_local().call(
                _call_local_llm, messages, temperature=temp, json_mode=jmode, role=role_str
            )
        except CircuitBreakerOpen:
            LLM_CIRCUIT_TRIPS.labels(backend="local_llm", role=role_str).inc()
            LLM_CALLS.labels(role=role_str, backend="local", status="circuit_open").inc()
            logger.warning("Local LLM circuit OPEN for role=%s — trying Gemini fallback", role_str)
            try:
                return await _call_gemini_with_retry(
                    messages, temperature=temp, json_mode=jmode, role=role_str,
                    max_retries=cfg.gemini_http_retries, backoff_s=cfg.gemini_http_retry_backoff_s,
                )
            except (CircuitBreakerOpen, Exception) as gemini_exc:
                if isinstance(gemini_exc, CircuitBreakerOpen):
                    LLM_CIRCUIT_TRIPS.labels(backend="gemini", role=role_str).inc()
                    LLM_CALLS.labels(role=role_str, backend="gemini", status="circuit_open").inc()
                logger.warning("Both LLM backends unavailable for role=%s — structured fallback", role_str)
                return _LLM_FALLBACK
        except Exception as exc:
            logger.warning("Local LLM failed for role=%s: %s — Gemini fallback", role_str, exc)
            try:
                return await _call_gemini_with_retry(
                    messages, temperature=temp, json_mode=jmode, role=role_str,
                    max_retries=cfg.gemini_http_retries, backoff_s=cfg.gemini_http_retry_backoff_s,
                )
            except (CircuitBreakerOpen, Exception) as gemini_exc:
                if isinstance(gemini_exc, CircuitBreakerOpen):
                    LLM_CIRCUIT_TRIPS.labels(backend="gemini", role=role_str).inc()
                logger.warning("Gemini fallback also failed for role=%s: %s", role_str, gemini_exc)
                return _LLM_FALLBACK

    # backend == "gemini"
    try:
        return await _call_gemini_with_retry(
            messages, temperature=temp, json_mode=jmode, role=role_str,
            max_retries=cfg.gemini_http_retries, backoff_s=cfg.gemini_http_retry_backoff_s,
        )
    except CircuitBreakerOpen:
        LLM_CIRCUIT_TRIPS.labels(backend="gemini", role=role_str).inc()
        LLM_CALLS.labels(role=role_str, backend="gemini", status="circuit_open").inc()
        logger.warning("Gemini circuit OPEN for role=%s — trying local LLM fallback", role_str)
        try:
            return await _get_cb_local().call(
                _call_local_llm, messages, temperature=temp, json_mode=jmode, role=role_str
            )
        except (CircuitBreakerOpen, Exception) as local_exc:
            if isinstance(local_exc, CircuitBreakerOpen):
                LLM_CIRCUIT_TRIPS.labels(backend="local_llm", role=role_str).inc()
            logger.warning("Both backends unavailable for role=%s — structured fallback", role_str)
            return _LLM_FALLBACK
    except Exception as exc:
        logger.warning("Gemini failed for role=%s: %s — local LLM fallback", role_str, exc)
        try:
            return await _get_cb_local().call(
                _call_local_llm, messages, temperature=temp, json_mode=jmode, role=role_str
            )
        except (CircuitBreakerOpen, Exception) as local_exc:
            if isinstance(local_exc, CircuitBreakerOpen):
                LLM_CIRCUIT_TRIPS.labels(backend="local_llm", role=role_str).inc()
            logger.warning("Local LLM fallback also failed for role=%s: %s", role_str, local_exc)
            return _LLM_FALLBACK


# ---------------------------------------------------------------------------
# Token usage persistence — fire-and-forget, non-blocking
# ---------------------------------------------------------------------------

async def _persist_token_usage(
    *,
    role: str,
    backend: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    total_tokens: int,
    duration_ms: int,
    dossier_id: int | None,
    session_id: str | None,
) -> None:
    """Persist actual token usage to DB. Called via asyncio.create_task — never blocks llm_call."""
    try:
        from app.core.database import async_session_factory
        from app.models.entities import LlmTokenUsage

        async with async_session_factory() as session:
            row = LlmTokenUsage(
                role=role,
                backend=backend,
                model=model,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                duration_ms=duration_ms,
                dossier_id=dossier_id,
                session_id=session_id,
            )
            session.add(row)
            await session.commit()
    except Exception as exc:
        logger.debug("Token usage persist failed (non-critical): %s", exc)


# ---------------------------------------------------------------------------
# Convenience: expose role registry for FE dashboard / meta endpoint
# ---------------------------------------------------------------------------

def get_model_registry() -> list[dict[str, Any]]:
    """Return list of all agent roles and their assigned models for the AI dashboard."""
    return [
        {
            "role":        role,
            "label":       cfg["label"],
            "backend":     cfg["backend"],
            "description": cfg["description"],
            "temperature": cfg["temperature"],
        }
        for role, cfg in _ROLE_CONFIG.items()
    ]
