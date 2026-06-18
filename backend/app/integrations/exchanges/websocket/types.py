from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any


class StreamChannel(StrEnum):
    TICKER = "ticker"
    CANDLES = "candles"
    ORDER_BOOK = "order_book"
    TRADES = "trades"
    BALANCE = "balance"
    POSITIONS = "positions"


@dataclass
class StreamMessage:
    exchange_id: str
    channel: str
    symbol: str
    data: dict[str, Any]
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WebSocketConfig:
    reconnect_interval: float = 1.0
    max_reconnect_attempts: int = 10
    ping_interval: float = 30.0
    backoff_factor: float = 2.0
    backoff_max: float = 60.0
