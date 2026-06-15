from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class SignalType(str, Enum):
    buy = "BUY"
    sell = "SELL"
    hold = "HOLD"


class OrderSide(str, Enum):
    buy = "BUY"
    sell = "SELL"


class OrderStatus(str, Enum):
    new = "NEW"
    partial = "PARTIAL"
    filled = "FILLED"
    canceled = "CANCELED"
    rejected = "REJECTED"


class PositionStatus(str, Enum):
    open = "OPEN"
    closed = "CLOSED"
    liquidated = "LIQUIDATED"


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "USDT"

    def __add__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError("Cannot add different currencies")
        return Money(self.amount + other.amount, self.currency)

    def __sub__(self, other: Money) -> Money:
        if self.currency != other.currency:
            raise ValueError("Cannot subtract different currencies")
        return Money(self.amount - other.amount, self.currency)

    def to_float(self) -> float:
        return float(self.amount)


@dataclass(frozen=True)
class Quantity:
    value: Decimal

    def to_float(self) -> float:
        return float(self.value)


@dataclass(frozen=True)
class Price:
    value: Decimal

    def to_float(self) -> float:
        return float(self.value)

    def __mul__(self, quantity: Quantity) -> Money:
        return Money(self.value * quantity.value)


@dataclass(frozen=True)
class RiskScore:
    value: float  # 0.0 to 100.0

    def is_acceptable(self, threshold: float = 80.0) -> bool:
        return self.value <= threshold


@dataclass(frozen=True)
class Confidence:
    value: float  # 0.0 to 100.0

    def is_high(self, threshold: float = 70.0) -> bool:
        return self.value >= threshold