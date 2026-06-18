from __future__ import annotations

from typing import Any

from app.domain.entities.strategy import StrategyType
from app.domain.strategies.base import StrategyPlugin
from app.domain.strategies.types import ConfigValidation, SignalResult, SignalType, StrategyMetadata


class BreakoutPlugin(StrategyPlugin):
    """Breakout strategy based on support/resistance levels and volume."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._lookback_periods: int = 20
        self._breakout_threshold: float = 0.02
        self._volume_multiplier: float = 1.5

    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="Breakout",
            version="1.0.0",
            strategy_type=StrategyType.breakout,
            description="Enters positions on breakout of support/resistance levels with volume confirmation",
            author="APEX Core",
            min_lookback_periods=30,
            supported_assets=["BTC", "ETH", "SOL", "SPX", "NDX"],
            supported_timeframes=["5m", "15m", "1h", "4h", "1d"],
        )

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._lookback_periods = config.get("lookback_periods", 20)
        self._breakout_threshold = config.get("breakout_threshold", 0.02)
        self._volume_multiplier = config.get("volume_multiplier", 1.5)

    def validate_config(self, config: dict[str, Any]) -> ConfigValidation:
        errors = []
        if "lookback_periods" in config:
            if not isinstance(config["lookback_periods"], int) or config["lookback_periods"] < 5:
                errors.append("lookback_periods must be a positive integer >= 5")
        if "breakout_threshold" in config:
            if not isinstance(config["breakout_threshold"], (int, float)) or config["breakout_threshold"] <= 0:
                errors.append("breakout_threshold must be a positive number")
        if "volume_multiplier" in config:
            if not isinstance(config["volume_multiplier"], (int, float)) or config["volume_multiplier"] <= 0:
                errors.append("volume_multiplier must be a positive number")
        return ConfigValidation(valid=len(errors) == 0, errors=errors)

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "lookback_periods": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 100,
                    "default": 20,
                    "description": "Periods to calculate support/resistance",
                },
                "breakout_threshold": {
                    "type": "number",
                    "minimum": 0.001,
                    "maximum": 0.1,
                    "default": 0.02,
                    "description": "Minimum percentage breakout from range",
                },
                "volume_multiplier": {
                    "type": "number",
                    "minimum": 1.0,
                    "maximum": 5.0,
                    "default": 1.5,
                    "description": "Volume must exceed average by this multiplier",
                },
            },
            "required": [],
        }

    def analyze(self, market_data: dict[str, Any]) -> SignalResult | None:
        candles = market_data.get("candles", [])
        if len(candles) < self._lookback_periods + 2:
            return None

        lookback = candles[-(self._lookback_periods + 1) : -1]
        current = candles[-1]
        prev = candles[-2]

        highs = [c["high"] for c in lookback]
        lows = [c["low"] for c in lookback]
        volumes = [c["volume"] for c in lookback]

        resistance = max(highs)
        support = min(lows)
        avg_volume = sum(volumes) / len(volumes) if volumes else 0

        current_price = current["close"]
        current_volume = current["volume"]

        resistance_breakout = (
            current_price > resistance * (1 + self._breakout_threshold)
            and current_volume > avg_volume * self._volume_multiplier
            and prev["close"] < resistance
        )

        support_breakdown = (
            current_price < support * (1 - self._breakout_threshold)
            and current_volume > avg_volume * self._volume_multiplier
            and prev["close"] > support
        )

        if resistance_breakout:
            stop_loss = resistance
            take_profit = current_price + (current_price - resistance) * 2
            return SignalResult(
                signal_type=SignalType.BUY,
                confidence=70.0,
                reason=f"Resistance breakout: price({current_price:.2f}) > resistance({resistance:.2f})",
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={"resistance": resistance, "avg_volume": avg_volume},
            )

        if support_breakdown:
            stop_loss = support
            take_profit = current_price - (support - current_price) * 2
            return SignalResult(
                signal_type=SignalType.SELL,
                confidence=70.0,
                reason=f"Support breakdown: price({current_price:.2f}) < support({support:.2f})",
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={"support": support, "avg_volume": avg_volume},
            )

        return None