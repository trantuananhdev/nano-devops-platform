"""
Five independent Gemini mini-agents — one API key each (GEMINI_API_KEY_1..5).

| Key | Role              | Used by                          |
|-----|-------------------|----------------------------------|
| 1   | traffic           | Demo burst traffic analyst       |
| 2   | crm_extract       | Worker lead extraction + auto-reply|
| 3   | odoo              | Department-head brief for Odoo   |
| 4   | telegram_reply    | Telegram auto-reply to customer  |
| 5   | telegram_analyze  | Telegram conversation → CRM      |
| 6   | compliance_guard  | Guardrails for replies/brief     |
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from config import GEMINI_API_KEYS, get_agent_key

if TYPE_CHECKING:
    from geminiProvider import GeminiProvider


class AgentRole(str, Enum):
    TRAFFIC = "traffic"
    CRM_EXTRACT = "crm_extract"
    ODOO = "odoo"
    TELEGRAM_REPLY = "telegram_reply"
    TELEGRAM_ANALYZE = "telegram_analyze"
    COMPLIANCE_GUARD = "compliance_guard"


_ROLE_INDEX = {
    AgentRole.TRAFFIC: 0,
    AgentRole.CRM_EXTRACT: 1,
    AgentRole.ODOO: 2,
    AgentRole.TELEGRAM_REPLY: 3,
    AgentRole.TELEGRAM_ANALYZE: 4,
    AgentRole.COMPLIANCE_GUARD: 5,
}

_providers: dict[AgentRole, "GeminiProvider"] = {}


def get_agent(role: AgentRole) -> "GeminiProvider":
    """Return a Gemini provider bound to this agent's dedicated API key."""
    from geminiProvider import create_gemini_provider

    if role not in _providers:
        idx = _ROLE_INDEX[role]
        api_key = get_agent_key(idx)
        _providers[role] = create_gemini_provider(api_key=api_key)
    return _providers[role]


def agent_key_count() -> int:
    return len(GEMINI_API_KEYS)
