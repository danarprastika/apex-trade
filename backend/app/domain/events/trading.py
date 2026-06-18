from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


@dataclass
class DomainEvent:
    type: str
    payload: dict[str, Any]
    id: str = field(default_factory=lambda: str(uuid4()))
    occurred_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    correlation_id: str | None = None
    source: str | None = None
    priority: int = 0


@dataclass
class SignalGenerated(DomainEvent):
    def __init__(self, strategy_id: str, signal: dict[str, Any], confidence: float, market_data: dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.strategy_id = strategy_id
        self.signal = signal
        self.confidence = confidence
        self.market_data = market_data


@dataclass
class OrderCreated(DomainEvent):
    def __init__(self, order_id: str, signal_id: str | None, params: dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.order_id = order_id
        self.signal_id = signal_id
        self.params = params


@dataclass
class OrderFilled(DomainEvent):
    def __init__(self, order_id: str, fill_price: float, fill_qty: float, **kwargs):
        super().__init__(**kwargs)
        self.fill_price = fill_price
        self.fill_qty = fill_qty


@dataclass
class PositionOpened(DomainEvent):
    def __init__(self, position_id: str, trade_id: str, entry: dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.position_id = position_id
        self.trade_id = trade_id
        self.entry = entry


@dataclass
class PositionClosed(DomainEvent):
    def __init__(self, position_id: str, exit_price: float, realized_pnl: float, **kwargs):
        super().__init__(**kwargs)
        self.exit_price = exit_price
        self.realized_pnl = realized_pnl


@dataclass
class RiskViolated(DomainEvent):
    def __init__(self, user_id: str, limit_type: str, current: float, threshold: float, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self.limit_type = limit_type
        self.current = current
        self.threshold = threshold


__all__ = [
    "DomainEvent",
    "SignalGenerated",
    "OrderCreated",
    "OrderFilled",
    "PositionOpened",
    "PositionClosed",
    "RiskViolated",
]