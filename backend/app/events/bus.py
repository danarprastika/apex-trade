from collections import defaultdict
from collections.abc import Awaitable, Callable

from app.events.types import ApexEvent

EventHandler = Callable[[ApexEvent], Awaitable[None] | None]


class EventBus:
    def __init__(self):
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: ApexEvent) -> None:
        for handler in self._handlers.get(event.type, []):
            result = handler(event)
            if hasattr(result, "__await__"):
                await result
