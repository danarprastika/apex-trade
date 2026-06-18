from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Protocol, runtime_checkable

from .types import StreamMessage


@runtime_checkable
class WebSocketMessage(Protocol):
    channel: str
    symbol: str
    data: dict[str, object]
    timestamp: str
    exchange_id: str


StreamCallback = Callable[[StreamMessage], Awaitable[None] | None]
