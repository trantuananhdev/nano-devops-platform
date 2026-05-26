"""Kịch bản đổ traffic — trung tâm tiếp nhận TNT (demo presenter)."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Optional

from demo_templates import build_webhook_body, pick_template

logger = logging.getLogger(__name__)

_SCENARIOS_PATH = Path(__file__).parent / "scenarios.json"
if not _SCENARIOS_PATH.exists():
    _alt = Path(__file__).resolve().parents[1] / "crm-demo-simulator" / "scenarios.json"
    _SCENARIOS_PATH = _alt if _alt.exists() else Path("/app/scenarios.json")
_cache: list[dict[str, Any]] | None = None


def load_scenarios() -> list[dict[str, Any]]:
    global _cache
    if _cache is None:
        with _SCENARIOS_PATH.open(encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache


def get_scenario(scenario_id: str) -> Optional[dict[str, Any]]:
    for s in load_scenarios():
        if s.get("id") == scenario_id:
            return s
    return None


def _channels_for_scenario(s: dict[str, Any]) -> list[str]:
    explicit = s.get("channels")
    if isinstance(explicit, list) and explicit:
        return explicit
    seen: list[str] = []
    for msg in s.get("messages") or []:
        ch = msg.get("channel", "generic")
        if ch not in seen:
            seen.append(ch)
    return seen


def list_scenarios_public() -> list[dict[str, Any]]:
    """Metadata for UI — không expose full message list nếu không cần."""
    out = []
    for s in load_scenarios():
        out.append(
            {
                "id": s["id"],
                "title_vi": s.get("title_vi", s["id"]),
                "description_vi": s.get("description_vi", ""),
                "crm_stage_vi": s.get("crm_stage_vi", ""),
                "ai_focus_vi": s.get("ai_focus_vi", ""),
                "icon": s.get("icon", "📩"),
                "channels": _channels_for_scenario(s),
                "message_count": len(s.get("messages") or []),
                "delay_ms": s.get("delay_ms", 500),
            }
        )
    return out


async def run_traffic_burst(
    scenario_id: str,
    handle_webhook_fn,
) -> dict[str, Any]:
    """
    Đổ lô tin theo kịch bản (giống traffic ập vào 1 trang Fanpage/Shop).
    handle_webhook_fn: async (channel, WebhookBody, secret) -> dict
    """
    from main import WebhookBody

    scenario = get_scenario(scenario_id)
    if not scenario:
        raise ValueError(f"unknown_scenario:{scenario_id}")

    messages = scenario.get("messages") or []
    delay_s = max(0, int(scenario.get("delay_ms", 500))) / 1000.0
    accepted: list[str] = []

    for i, spec in enumerate(messages):
        if i > 0 and delay_s > 0:
            await asyncio.sleep(delay_s)
        channel = spec.get("channel", "generic")
        template = pick_template(
            channel,
            template_id=spec.get("template_id"),
            category=spec.get("category"),
        )
        overrides = dict(spec.get("overrides") or {})
        payload = build_webhook_body(template, channel, overrides)
        body = WebhookBody(**payload)
        try:
            result = await handle_webhook_fn(channel, body, None)
            mid = result.get("message_id") or result.get("job_id")
            if mid and not result.get("duplicate"):
                accepted.append(mid)
        except Exception as exc:
            logger.warning("Burst message failed %s: %s", spec.get("template_id"), exc)

    return {
        "status": "burst_started",
        "scenario_id": scenario_id,
        "title_vi": scenario.get("title_vi"),
        "accepted_count": len(accepted),
        "message_ids": accepted,
        "total_planned": len(messages),
    }
