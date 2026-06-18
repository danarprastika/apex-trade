from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from app.events.types import ApexEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[ApexEvent], Awaitable[None] | None]


class EventBus:
    """Central event bus using Redis Streams for persistence."""

    def __init__(self, redis_client: Any | None = None) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._redis = redis_client
        self._running = False

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        normalized_type = event_type.upper().replace(".", "_")
        self._handlers[normalized_type].append(handler)
        logger.info("Subscribed to event type=%s", normalized_type)

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        if event_type in self._handlers:
            self._handlers[event_type] = [h for h in self._handlers[event_type] if h != handler]

    async def publish(self, event: ApexEvent) -> None:
        event_type = event.type.upper().replace(".", "_")
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                result = handler(event)
                if asyncio.iscoroutine(result):
                    await result
            except Exception as e:
                logger.exception("Event handler error type=%s", event_type)

    async def publish_to_stream(self, event: ApexEvent, stream: str = "events") -> None:
        if self._redis:
            await self._redis.xadd(stream, {"type": event.type, "payload": event.payload})

    async def start_consuming(self, stream: str = "events", group: str = "apex-consumer") -> None:
        """Start consuming events from Redis stream in background."""
        if not self._redis:
            logger.warning("Redis not configured, cannot consume from stream")
            return

        self._running = True
        while self._running:
            try:
                messages = await self._redis.xreadgroup(
                    groupname=group,
                    consumername=f"consumer-{id(self)}",
                    streams={stream: ">"},
                    count=10,
                    block=1000,
                )
                for stream_name, msg_list in messages:
                    for msg_id, msg_data in msg_list:
                        await self._process_stream_message(msg_data)
                        await self._redis.xack(stream, group, msg_id)
            except Exception as e:
                logger.exception("Error consuming from stream")
                await asyncio.sleep(1)

    async def _process_stream_message(self, msg_data: dict) -> None:
        event_type = msg_data.get("type", "")
        payload = msg_data.get("payload", {})
        event = ApexEvent(type=event_type, payload=payload)
        await self.publish(event)

    def stop(self) -> None:
        self._running = False