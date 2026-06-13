"""Seed realistic LLM token usage data for the Token Usage dashboard.

Generates 30 days of historical data across all 9 roles and 2 backends.
Reflects realistic usage patterns:
  - Gemini roles (LEGAL, FINANCIAL, OCR, CRITIC, TOOL_MOCK): higher token counts
  - Local roles (PLANNER, EXECUTOR, REFLECTOR, SUMMARY): lower counts, 0 cost
  - Hồ sơ 198/TTr-EVNHANOI (dossier_id=1) is the most active
"""

import asyncio
import random
from datetime import datetime, timedelta, timezone

from app.core.database import async_session_factory
from app.models.entities import LlmTokenUsage

# Token range per role (prompt, completion) — based on real Gemini/llama behavior
_ROLE_RANGES = {
    "planner":   {"backend": "local",  "model": "gemma-4-8b-it", "p": (800, 2200),  "c": (300, 900)},
    "executor":  {"backend": "local",  "model": "gemma-4-8b-it", "p": (400, 1200),  "c": (100, 400)},
    "reflector": {"backend": "local",  "model": "gemma-4-8b-it", "p": (1200, 3000), "c": (200, 600)},
    "summary":   {"backend": "local",  "model": "gemma-4-8b-it", "p": (2000, 5000), "c": (800, 2000)},
    "legal":     {"backend": "gemini", "model": "gemini-2.5-flash", "p": (1500, 4000), "c": (500, 1500)},
    "financial": {"backend": "gemini", "model": "gemini-2.5-flash", "p": (1000, 3000), "c": (300, 1000)},
    "ocr":       {"backend": "gemini", "model": "gemini-2.5-flash", "p": (3000, 8000), "c": (200, 800)},
    "critic":    {"backend": "gemini", "model": "gemini-2.5-flash", "p": (2500, 6000), "c": (600, 1800)},
    "tool_mock": {"backend": "gemini", "model": "gemini-2.5-flash", "p": (600, 1800),  "c": (200, 600)},
}

_DOSSIER_IDS = [1, 2, 3, 4, 5, None]  # None = non-dossier calls (health, test)
_DOSSIER_WEIGHTS = [0.40, 0.15, 0.12, 0.10, 0.08, 0.15]  # dossier_id=1 most active

_SESSION_PREFIX = "seed-session-"


async def seed_token_usage() -> None:
    async with async_session_factory() as session:
        # Check if already seeded
        from sqlalchemy import select, func
        count = (await session.execute(select(func.count(LlmTokenUsage.id)))).scalar()
        if count and count > 50:
            print(f"[seed_token_usage] Already seeded ({count} rows), skipping.")
            return

        rows = []
        now = datetime.now(tz=timezone.utc)
        rng = random.Random(42)  # deterministic

        for day_offset in range(30, 0, -1):
            day_base = now - timedelta(days=day_offset)
            # Vary activity level per day (weekends lighter)
            weekday = day_base.weekday()
            calls_per_day = rng.randint(8, 20) if weekday < 5 else rng.randint(2, 8)

            for _ in range(calls_per_day):
                role = rng.choice(list(_ROLE_RANGES.keys()))
                cfg = _ROLE_RANGES[role]
                prompt_t = rng.randint(*cfg["p"])
                compl_t  = rng.randint(*cfg["c"])
                dossier_id = rng.choices(_DOSSIER_IDS, weights=_DOSSIER_WEIGHTS, k=1)[0]

                # Random time within the day
                ts = day_base.replace(
                    hour=rng.randint(7, 18),
                    minute=rng.randint(0, 59),
                    second=rng.randint(0, 59),
                )

                rows.append(LlmTokenUsage(
                    role=role,
                    backend=cfg["backend"],
                    model=cfg["model"],
                    prompt_tokens=prompt_t,
                    completion_tokens=compl_t,
                    total_tokens=prompt_t + compl_t,
                    duration_ms=rng.randint(400, 8000),
                    dossier_id=dossier_id,
                    session_id=f"{_SESSION_PREFIX}{rng.randint(1, 20)}",
                    created_at=ts,
                ))

        session.add_all(rows)
        await session.commit()
        print(f"[seed_token_usage] Seeded {len(rows)} token usage rows (30 days).")


if __name__ == "__main__":
    asyncio.run(seed_token_usage())
