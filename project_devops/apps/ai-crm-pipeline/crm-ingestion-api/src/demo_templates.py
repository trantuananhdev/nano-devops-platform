"""Demo message templates BDS — các mẫu tin nhắn khách hàng bất động sản trên đa kênh."""

from __future__ import annotations

import json
import random
import uuid
from pathlib import Path
from typing import Any, Optional

_TEMPLATES_PATH = Path(__file__).parent / "templates.json"
if not _TEMPLATES_PATH.exists():
    _TEMPLATES_PATH = Path(__file__).resolve().parents[1] / "crm-demo-simulator" / "templates.json"
_cache: list[dict[str, Any]] | None = None


def load_templates() -> list[dict[str, Any]]:
    global _cache
    if _cache is None:
        with _TEMPLATES_PATH.open(encoding="utf-8") as f:
            data = json.load(f)
        _cache = data if isinstance(data, list) else data.get("templates", [])
    return _cache


def get_template(template_id: str) -> Optional[dict[str, Any]]:
    for t in load_templates():
        if t.get("id") == template_id:
            return t
    return None


def pick_template(
    channel: str,
    template_id: Optional[str] = None,
    category: Optional[str] = None,
) -> dict[str, Any]:
    templates = load_templates()
    if template_id:
        found = get_template(template_id)
        if found:
            return found

    pool = [t for t in templates if t.get("channel", "generic") in (channel, "generic")]
    if category:
        pool = [t for t in pool if t.get("category") == category] or pool
    if not pool:
        pool = templates
    return random.choice(pool)


def build_webhook_body(
    template: dict[str, Any],
    channel: str,
    overrides: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    overrides = overrides or {}
    msg_id = overrides.get("message_id") or f"{channel}-{uuid.uuid4().hex[:12]}"
    body: dict[str, Any] = {
        "message_id": msg_id,
        "raw_text": template["raw_text"],
        "channel": channel,
        "locale": template.get("locale"),
        "demo_category": template.get("category"),
        "property_type": template.get("property_type") or overrides.get("property_type"),
        "location": overrides.get("location") or template.get("location"),
        "sender_id": overrides.get("sender_id") or f"demo_{channel}_{uuid.uuid4().hex[:6]}",
        "customer_name": overrides.get("customer_name") or template.get("demo_customer_name"),
        "phone": overrides.get("phone") or template.get("demo_phone"),
        }
    if channel == "shopee":
        body["order_id"] = overrides.get("order_id") or f"24{random.randint(100000000, 999999999)}"
        body["shop_id"] = overrides.get("shop_id") or "bds_official"
    if channel == "tiktok" and template.get("shop_id"):
        body["shop_id"] = template["shop_id"]
    if channel == "facebook":
        body["page_id"] = overrides.get("page_id") or "page_bds_demo"
    if channel == "zalo":
        body["page_id"] = overrides.get("page_id") or "oa_bds_demo"
    if channel == "instagram":
        body["page_id"] = overrides.get("page_id") or "ig_bds_demo"
    body.update({k: v for k, v in overrides.items() if k not in body})
    return body
