#!/usr/bin/env python3
"""CLI lead simulator — sends demo webhooks at a controlled rate."""

from __future__ import annotations

import argparse
import asyncio
import json
import random
import sys
import uuid
from pathlib import Path

import httpx

TEMPLATES_PATH = Path(__file__).parent / "templates.json"
CHANNEL_PATHS = {
    "facebook": "/webhook/facebook",
    "tiktok": "/webhook/tiktok",
    "shopee": "/webhook/shopee",
    "generic": "/webhook/generic",
}


def load_templates() -> list[dict]:
    with TEMPLATES_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def pick_template(templates: list[dict], channel: str, locale_mix: list[str]) -> dict:
    pool = [t for t in templates if t.get("channel") == channel]
    if locale_mix:
        loc_pool = [t for t in pool if any(t.get("locale", "").startswith(l) for l in locale_mix)]
        if loc_pool:
            pool = loc_pool
    if not pool:
        pool = [t for t in templates if t.get("channel") == "generic"] or templates
    weights = [t.get("weight", 1) for t in pool]
    return random.choices(pool, weights=weights, k=1)[0]


def build_body(template: dict, channel: str) -> dict:
    body = {
        "message_id": f"sim-{channel}-{uuid.uuid4().hex[:10]}",
        "raw_text": template["raw_text"],
        "channel": channel,
        "locale": template.get("locale"),
        "sender_id": f"sim_user_{random.randint(1000, 9999)}",
        "timestamp": "2026-05-25T12:00:00Z",
    }
    if channel == "shopee":
        body["order_id"] = f"24{random.randint(100000000, 999999999)}"
        body["shop_id"] = "tnt_official"
    if channel == "tiktok":
        body["shop_id"] = "tnt_id_shop"
    if channel == "facebook":
        body["page_id"] = "page_tnt_demo"
    return body


async def send_one(
    client: httpx.AsyncClient,
    base_url: str,
    channel: str,
    template: dict,
    secret: str | None,
) -> int:
    path = CHANNEL_PATHS.get(channel, CHANNEL_PATHS["generic"])
    headers = {"Content-Type": "application/json"}
    if secret:
        headers["X-Webhook-Secret"] = secret
    body = build_body(template, channel)
    resp = await client.post(f"{base_url.rstrip('/')}{path}", json=body, headers=headers)
    return resp.status_code


async def run_sim(args: argparse.Namespace) -> None:
    templates = load_templates()
    channels = [c.strip() for c in args.channels.split(",") if c.strip()]
    locale_mix = [l.strip() for l in args.locale_mix.split(",") if l.strip()]
    interval = 1.0 / max(args.rate, 0.1)
    end_at = asyncio.get_event_loop().time() + args.duration
    sent = 0
    errors = 0

    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        while asyncio.get_event_loop().time() < end_at:
            batch = channels if not args.burst else channels * min(args.burst, 10)
            tasks = []
            for ch in batch:
                tpl = pick_template(templates, ch, locale_mix)
                tasks.append(send_one(client, args.base_url, ch, tpl, args.secret))
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception) or r >= 400:
                    errors += 1
                else:
                    sent += 1
            await asyncio.sleep(interval)

    print(f"Done: sent_ok={sent} errors={errors} rate={args.rate}/s duration={args.duration}s")


def main() -> None:
    p = argparse.ArgumentParser(description="TNT CRM lead simulator")
    p.add_argument("--base-url", default="https://crm-ingest.nano.platform")
    p.add_argument("--rate", type=float, default=2.0, help="Messages per second")
    p.add_argument("--duration", type=int, default=60, help="Seconds")
    p.add_argument("--channels", default="facebook,tiktok,shopee")
    p.add_argument("--locale-mix", default="tl,id,ms")
    p.add_argument("--burst", type=int, default=0, help="Parallel sends per tick")
    p.add_argument("--secret", default=None, help="X-Webhook-Secret if configured")
    args = p.parse_args()
    try:
        asyncio.run(run_sim(args))
    except KeyboardInterrupt:
        print("Stopped", file=sys.stderr)


if __name__ == "__main__":
    main()
