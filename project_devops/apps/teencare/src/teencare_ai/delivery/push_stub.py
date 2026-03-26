from __future__ import annotations

from dataclasses import dataclass

from teencare_ai.delivery.types import DeliveryPayload


@dataclass(frozen=True)
class PushResult:
    ok: bool
    provider_message_id: str | None = None
    error: str | None = None


class PushProvider:
    def send(self, *, parent_id: str, payload: DeliveryPayload) -> PushResult:
        raise NotImplementedError


class NoopPushProvider(PushProvider):
    """
    MVP stub: records "sent" without external side effects.
    Replace with FCM/APNs integration in Phase 1 delivery work.
    """

    def send(self, *, parent_id: str, payload: DeliveryPayload) -> PushResult:
        _ = parent_id, payload
        return PushResult(ok=True, provider_message_id="noop")

