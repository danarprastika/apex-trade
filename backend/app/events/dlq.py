from __future__ import annotations

import logging
from typing import Any

from app.events.types import ApexEvent

logger = logging.getLogger(__name__)

MAX_RETRIES = 5


class DeadLetterQueue:
    """Manages failed events after max retry attempts."""

    def __init__(self, redis_client: Any | None = None) -> None:
        self._redis = redis_client
        self._failed_events: list[dict[str, Any]] = []

    def push(self, event: ApexEvent, error: str, handler_name: str) -> None:
        failed_event = {
            "event_id": event.id,
            "event_type": event.type,
            "error": error,
            "handler": handler_name,
            "retry_count": MAX_RETRIES,
            "payload": event.payload,
        }
        self._failed_events.append(failed_event)
        logger.error("Event pushed to DLQ event_id=%s error=%s", event.id, error)

    def get_failed(self, limit: int = 100) -> list[dict[str, Any]]:
        return self._failed_events[:limit]

    def clear(self, event_id: str | None = None) -> None:
        if event_id:
            self._failed_events = [e for e in self._failed_events if e.get("event_id") != event_id]
        else:
            self._failed_events.clear()

    async def requeue(self, event_id: str) -> ApexEvent | None:
        for i, event in enumerate(self._failed_events):
            if event.get("event_id") == event_id:
                del self._failed_events[i]
                return ApexEvent(type=event["event_type"], payload=event["payload"])
        return None