"""
Port of ai-agent/src/llm/providerFactory.js — CRM worker uses Gemini only.
"""

from __future__ import annotations

import os

from geminiProvider import create_gemini_provider


def create_llm_provider():
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    if provider in ("google", "gemini"):
        return create_gemini_provider()
    raise ValueError(f"Unsupported LLM_PROVIDER for CRM demo: {provider}")
