from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone


def parse_time_slot(time_slot: str) -> tuple[time, time]:
    """
    Expected formats:
    - "HH:MM-HH:MM"
    - "HH:MM - HH:MM"
    """
    raw = (time_slot or "").strip().replace(" ", "")
    if "-" not in raw:
        raise ValueError("Invalid time_slot format. Expected 'HH:MM-HH:MM'.")
    start_s, end_s = raw.split("-", 1)
    h1, m1 = start_s.split(":")
    h2, m2 = end_s.split(":")
    start_t = time(int(h1), int(m1))
    end_t = time(int(h2), int(m2))
    if (end_t.hour, end_t.minute) <= (start_t.hour, start_t.minute):
        raise ValueError("Invalid time_slot: end must be after start.")
    return start_t, end_t


def time_slots_overlap(a: str, b: str) -> bool:
    a1, a2 = parse_time_slot(a)
    b1, b2 = parse_time_slot(b)
    return max(a1, b1) < min(a2, b2)


def next_occurrence_utc(day_of_week: int, time_slot: str, now: datetime | None = None) -> datetime:
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    start_t, _ = parse_time_slot(time_slot)
    # Map 0=Mon..6=Sun to Python weekday (0=Mon..6=Sun) => same
    days_ahead = (int(day_of_week) - now.weekday()) % 7
    candidate_date = (now.date() + timedelta(days=days_ahead))
    candidate_dt = datetime.combine(candidate_date, start_t, tzinfo=timezone.utc)
    if candidate_dt <= now:
        candidate_dt = candidate_dt + timedelta(days=7)
    return candidate_dt


def today_utc() -> date:
    return datetime.now(timezone.utc).date()


def should_refund_session(now: datetime, scheduled_at: datetime) -> bool:
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    if scheduled_at.tzinfo is None:
        scheduled_at = scheduled_at.replace(tzinfo=timezone.utc)
    return (scheduled_at - now) > timedelta(hours=24)

