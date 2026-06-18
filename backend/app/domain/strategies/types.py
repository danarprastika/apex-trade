from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

from app.domain.entities.strategy import StrategyType


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class StrategyMetadata:
    strategy_id: str | None = None
    name: str = ""
    version: str = "1.0"
    strategy_type: StrategyType = StrategyType.trend_following
    description: str = ""
    author: str = ""
    min_lookback_periods: int = 0
    supported_assets: list[str] = None
    supported_timeframes: list[str] = None

    def __post_init__(self):
        if self.supported_assets is None:
            self.supported_assets = []
        if self.supported_timeframes is None:
            self.supported_timeframes = []


@dataclass
class SignalResult:
    signal_type: SignalType
    confidence: float
    reason: str
    entry_price: float
    stop_loss: float | None
    take_profit: float | None
    metadata: dict[str, Any]


@dataclass
class ConfigValidation:
    valid: bool
    errors: list[str]


class PluginLifecycleState(str, Enum):
    discovered = "DISCOVERED"
    validated = "VALIDATED"
    loaded = "LOADED"
    registered = "REGISTERED"
    initialized = "INITIALIZED"
    activated = "ACTIVATED"
    deactivated = "DEACTIVATED"
    failed = "FAILED"
    unregistered = "UNREGISTERED"


class PluginHealthStatus(str, Enum):
    healthy = "HEALTHY"
    degraded = "DEGRADED"
    unhealthy = "UNHEALTHY"
    unknown = "UNKNOWN"


@dataclass
class PluginHealthSnapshot:
    code: str
    lifecycle_state: PluginLifecycleState
    health_status: PluginHealthStatus
    last_error: str | None = None
    executions: int = 0
    failures: int = 0
    last_execution_ms: float | None = None
    last_execution_at: datetime | None = None
    updated_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PluginExecutionRecord:
    code: str
    success: bool
    duration_ms: float
    error: str | None = None
