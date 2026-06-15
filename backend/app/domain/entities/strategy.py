from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID


class StrategyType(str, Enum):
    trend_following = "trend_following"
    mean_reversion = "mean_reversion"
    breakout = "breakout"
    arbitrage = "arbitrage"
    custom = "custom"


class StrategyStatus(str, Enum):
    active = "ACTIVE"
    inactive = "INACTIVE"
    archived = "ARCHIVED"


class Strategy:
    def __init__(
        self,
        id: str,
        name: str,
        code: str,
        version: str,
        strategy_type: StrategyType,
        status: StrategyStatus,
        description: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.name = name
        self.code = code
        self.version = version
        self.description = description
        self.strategy_type = strategy_type
        self.status = status
        self.created_at = created_at
        self.updated_at = updated_at

    def activate(self) -> None:
        self.status = StrategyStatus.active

    def deactivate(self) -> None:
        self.status = StrategyStatus.inactive

    def archive(self) -> None:
        self.status = StrategyStatus.archived