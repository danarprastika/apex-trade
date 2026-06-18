from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class KillSwitchScope(str, Enum):
    GLOBAL = "GLOBAL"
    USER = "USER"
    EXCHANGE = "EXCHANGE"
    STRATEGY = "STRATEGY"


class ValidationLayer(str, Enum):
    KILL_SWITCH = "kill_switch"
    MARKET_DATA_QUALITY = "market_data_quality"
    ORDER_SIZE_LIMIT = "order_size_limit"
    DAILY_LOSS_LIMIT = "daily_loss_limit"
    EXPOSURE_LIMIT = "exposure_limit"
    CIRCUIT_BREAKER = "circuit_breaker"


@dataclass(frozen=True)
class SafetyContext:
    user_id: str
    exchange_account_id: str
    strategy_id: str | None = None
    symbol: str | None = None
    side: str | None = None
    order_type: str | None = None
    quantity: float | None = None
    price: float | None = None
    idempotency_key: str | None = None
    correlation_id: str | None = None
    deadline: datetime | None = None


@dataclass
class SafetyDecision:
    approved: bool = True
    reasons: list[str] = None
    checks_performed: dict[str, bool] = None
    required_checks: list[str] = None
    execution_blocked_by: list[str] = None
    risk_score: float | None = None
    position_size: float | None = None

    def __post_init__(self):
        if self.reasons is None:
            self.reasons = []
        if self.checks_performed is None:
            self.checks_performed = {}
        if self.required_checks is None:
            self.required_checks = []
        if self.execution_blocked_by is None:
            self.execution_blocked_by = []

    def add_rejection(self, layer: ValidationLayer, reason: str) -> None:
        self.approved = False
        self.checks_performed[layer.value] = False
        self.execution_blocked_by.append(layer.value)
        self.reasons.append(reason)

    def add_success(self, layer: ValidationLayer) -> None:
        self.checks_performed[layer.value] = True

    @property
    def veto_reasons(self) -> list[str]:
        return self.reasons