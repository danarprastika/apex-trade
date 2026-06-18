from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class SlippageModel(str, Enum):
    FIXED = "FIXED"
    VOLUME_BASED = "VOLUME_BASED"
    VOLATILITY_BASED = "VOLATILITY_BASED"
    HISTORICAL = "HISTORICAL"


class CommissionModel(str, Enum):
    FLAT = "FLAT"
    EXCHANGE_TIER = "EXCHANGE_TIER"


@dataclass
class SlippageConfig:
    model: str
    max_slippage_pct: float = 0.001
    volume_threshold: float = 1.0


@dataclass
class CommissionConfig:
    model: str
    maker_fee: float = 0.001
    taker_fee: float = 0.001
    volume_tier: int = 1


class SlippageCalculator:
    def __init__(self, config: SlippageConfig):
        self.config = config

    def calculate(self, price: float, volume: float, avg_volume: float) -> float:
        if self.config.model == SlippageModel.FIXED:
            return price * self.config.max_slippage_pct

        if self.config.model == SlippageModel.VOLUME_BASED:
            volume_ratio = min(volume / avg_volume, 5.0) if avg_volume > 0 else 1.0
            slippage_pct = self.config.max_slippage_pct * volume_ratio
            return price * min(slippage_pct, self.config.max_slippage_pct * 3)

        if self.config.model == SlippageModel.VOLATILITY_BASED:
            volatility_factor = min(volume / 1000, 1.0) if volume > 0 else 0.5
            return price * self.config.max_slippage_pct * volatility_factor

        if self.config.model == SlippageModel.HISTORICAL:
            return price * self.config.max_slippage_pct

        return price * 0.001


class CommissionCalculator:
    def __init__(self, config: CommissionConfig):
        self.config = config

    def calculate(self, quantity: float, price: float, is_maker: bool = False) -> float:
        notional = quantity * price
        fee_rate = self.config.maker_fee if is_maker else self.config.taker_fee

        if self.config.model == CommissionModel.EXCHANGE_TIER:
            tier_multipliers = {1: 1.0, 2: 0.9, 3: 0.8, 4: 0.7}
            multiplier = tier_multipliers.get(self.config.volume_tier, 1.0)
            fee_rate *= multiplier

        return notional * fee_rate


class PositionSizingCalculator:
    def __init__(self, method: str, value: float):
        self.method = method
        self.value = value

    def calculate_quantity(self, capital: float, price: float, stop_loss: float | None = None) -> float:
        if self.method == "FIXED":
            return self.value

        if self.method == "PERCENTAGE":
            notional = capital * (self.value / 100)
            return notional / price if price > 0 else 0

        if self.method == "RISK_BASED":
            if stop_loss and stop_loss < price:
                risk_per_share = price - stop_loss
                return (capital * (self.value / 100)) / risk_per_share if risk_per_share > 0 else 0
            return (capital * (self.value / 100)) / price if price > 0 else 0

        return self.value / price if price > 0 else 0