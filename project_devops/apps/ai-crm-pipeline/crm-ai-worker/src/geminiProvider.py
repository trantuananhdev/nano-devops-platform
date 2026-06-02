"""
Port of ai-powered-development/ai-agent/src/llm/geminiProvider.js
Same REST API, env vars, and chatText({ messages }) contract.
"""

from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Optional

import httpx

from config import get_next_gemini_key, GEMINI_API_KEYS

logger = logging.getLogger(__name__)


@dataclass
class GeminiProvider:
    chat_text: Any
    model: str
    temperature: float
    max_tokens: int


def create_gemini_provider(*, api_key: str | None = None) -> GeminiProvider:
    if not GEMINI_API_KEYS and not api_key:
        raise RuntimeError("No Gemini API keys available. Please set GEMINI_API_KEY_1 to GEMINI_API_KEY_5 in .env")

    fixed_key = (api_key or "").strip() or None
    model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    api_version = os.getenv("GEMINI_API_VERSION", "v1beta")
    temperature = float(os.getenv("GEMINI_TEMPERATURE", "0.2"))
    max_tokens = int(os.getenv("GEMINI_MAX_TOKENS", "2048"))
    timeout_ms = int(os.getenv("GEMINI_TIMEOUT_MS", "60000"))

    def chat_text(
        *,
        messages: list[dict[str, str]],
        json_mode: bool = False,
    ) -> str:
        system_message = next((m for m in messages if m.get("role") == "system"), None)
        user_messages = [m for m in messages if m.get("role") != "system"]

        prompt = ""
        if system_message:
            prompt += f"[INSTRUCTION]\n{system_message['content']}\n\n"
        prompt += "\n\n".join(m["content"] for m in user_messages)

        generation_config: dict[str, Any] = {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        }
        if json_mode:
            generation_config["responseMimeType"] = "application/json"

        body = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": generation_config,
        }

        max_retries = int(os.getenv("GEMINI_HTTP_RETRIES", "3"))
        backoff_s = float(os.getenv("GEMINI_HTTP_RETRY_BACKOFF_S", "2"))

        with httpx.Client(timeout=timeout_ms / 1000.0) as client:
            resp = None
            for attempt in range(max_retries):
                # Get a fresh key for each retry
                use_key = fixed_key or get_next_gemini_key()
                url = (
                    f"https://generativelanguage.googleapis.com/{api_version}"
                    f"/models/{model}:generateContent?key={use_key}"
                )
                try:
                    resp = client.post(
                        url,
                        json=body,
                        headers={"Content-Type": "application/json"},
                    )
                    if resp.status_code == 200:
                        break
                    elif resp.status_code in (429, 403) and attempt + 1 < max_retries:
                        # Rate limit or quota exceeded - try next key
                        logger.warning(
                            "Gemini %d, trying new key and retry %d/%d in %.1fs",
                            resp.status_code,
                            attempt + 1,
                            max_retries,
                            backoff_s,
                        )
                        time.sleep(backoff_s)
                        continue
                    else:
                        resp.raise_for_status()
                except httpx.HTTPStatusError as e:
                    if attempt + 1 < max_retries and e.response.status_code in (429, 403):
                        logger.warning(
                            "Gemini error %d, trying new key and retry %d/%d in %.1fs",
                            e.response.status_code,
                            attempt + 1,
                            max_retries,
                            backoff_s,
                        )
                        time.sleep(backoff_s)
                        continue
                    raise
            assert resp is not None
            data = resp.json()

        try:
            text = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError):
            raise ValueError(
                f"Gemini returned empty or invalid response: {data}"
            ) from None

        if not text:
            raise ValueError(f"Gemini returned empty or invalid response: {data}")
        return text

    return GeminiProvider(
        chat_text=chat_text,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
    )
