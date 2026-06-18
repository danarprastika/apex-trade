from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable

from app.events.types import ApexEvent

EventHandler = Callable[[ApexEvent], Awaitable[None] | None]


class EventHandler:
    """Base class for event handlers with circuit breaker and retry logic."""

    def __init__(self, name: str, max_retries: int = 3, timeout_seconds: int = 30) -> None:
        self.name = name
        self.max_retries = max_retries
        self.timeout_seconds = timeout_seconds
        self._failure_count = 0
        self._circuit_open = False
        self._processed_events: set[str] = set()

    async def handle(self, event: ApexEvent) -> bool:
        if self._is_duplicate(event.id):
            return True

        for attempt in range(self.max_retries):
            try:
                await self.process(event)
                self._failure_count = 0
                self._record_processed(event.id)
                return True
            except Exception as e:
                self._failure_count += 1
                if attempt == self.max_retries - 1:
                    return False

        if self._failure_count >= 5:
            self._circuit_open = True
        return False

    def _is_duplicate(self, event_id: str) -> bool:
        return event_id in self._processed_events

    def _record_processed(self, event_id: str) -> None:
        self._processed_events.add(event_id)
        if len(self._processed_events) > 10000:
            self._processed_events.pop()

    async def process(self, event: ApexEvent) -> None:
        raise NotImplementedError