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

from config import _load_gemini_key

logger = logging.getLogger(__name__)


@dataclass
class GeminiProvider:
    chat_text: Any
    model: str
    temperature: float
    max_tokens: int


def create_gemini_provider() -> GeminiProvider:
    api_key = _load_gemini_key()
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY is not set")

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

        url = (
            f"https://generativelanguage.googleapis.com/{api_version}"
            f"/models/{model}:generateContent?key={api_key}"
        )

        max_retries = int(os.getenv("GEMINI_HTTP_RETRIES", "3"))
        backoff_s = float(os.getenv("GEMINI_HTTP_RETRY_BACKOFF_S", "2"))

        with httpx.Client(timeout=timeout_ms / 1000.0) as client:
            resp = None
            for attempt in range(max_retries):
                resp = client.post(
                    url,
                    json=body,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code == 429 and attempt + 1 < max_retries:
                    wait = backoff_s * (2**attempt)
                    logger.warning(
                        "Gemini 429, retry %d/%d in %.1fs",
                        attempt + 1,
                        max_retries,
                        wait,
                    )
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                break
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
