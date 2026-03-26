from __future__ import annotations

from typing import Literal, TypedDict


DeliveryChannel = Literal["push", "in_app"]


class DeliveryAction(TypedDict):
    label: str
    timing: str
    details: str


class DeliveryPayload(TypedDict, total=False):
    session_id: str
    channel: DeliveryChannel
    title: str
    summary_bullets: list[str]
    actions: list[DeliveryAction]
    risk_level: str
    confidence: str
    flag: str

