from __future__ import annotations

from typing import Any

from app.domain.entities.strategy import StrategyType
from app.domain.strategies.base import StrategyPlugin
from app.domain.strategies.types import ConfigValidation, SignalResult, SignalType, StrategyMetadata


class TrendFollowingPlugin(StrategyPlugin):
    """Trend following strategy based on moving average crossovers."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._fast_ma_period: int = 9
        self._slow_ma_period: int = 21
        self._confirmation_periods: int = 3

    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="Trend Following",
            version="1.0.0",
            strategy_type=StrategyType.trend_following,
            description="Identifies and follows market trends using moving average crossovers with volume confirmation",
            author="APEX Core",
            min_lookback_periods=50,
            supported_assets=["BTC", "ETH", "SOL", "XAUUSD", "SPX"],
            supported_timeframes=["1m", "5m", "15m", "1h", "4h", "1d"],
        )

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._fast_ma_period = config.get("fast_ma_period", 9)
        self._slow_ma_period = config.get("slow_ma_period", 21)
        self._confirmation_periods = config.get("confirmation_periods", 3)

    def validate_config(self, config: dict[str, Any]) -> ConfigValidation:
        errors = []
        if "fast_ma_period" in config:
            if not isinstance(config["fast_ma_period"], int) or config["fast_ma_period"] < 1:
                errors.append("fast_ma_period must be a positive integer")
        if "slow_ma_period" in config:
            if not isinstance(config["slow_ma_period"], int) or config["slow_ma_period"] < 1:
                errors.append("slow_ma_period must be a positive integer")
        if "confirmation_periods" in config:
            if not isinstance(config["confirmation_periods"], int) or config["confirmation_periods"] < 1:
                errors.append("confirmation_periods must be a positive integer")
        if (
            "fast_ma_period" in config
            and "slow_ma_period" in config
            and config["fast_ma_period"] >= config["slow_ma_period"]
        ):
            errors.append("fast_ma_period must be less than slow_ma_period")
        return ConfigValidation(valid=len(errors) == 0, errors=errors)

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "fast_ma_period": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "default": 9,
                    "description": "Fast moving average period",
                },
                "slow_ma_period": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 200,
                    "default": 21,
                    "description": "Slow moving average period",
                },
                "confirmation_periods": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 3,
                    "description": "Number of periods to confirm trend",
                },
            },
            "required": [],
        }

    def analyze(self, market_data: dict[str, Any]) -> SignalResult | None:
        candles = market_data.get("candles", [])
        if len(candles) < self._slow_ma_period:
            return None

        closes = [c["close"] for c in candles[-(self._slow_ma_period + 5) :]]
        fast_ma = self._calculate_ma(closes[-self._fast_ma_period:])
        slow_ma = self._calculate_ma(closes[-self._slow_ma_period:])
        fast_ma_prev = self._calculate_ma(closes[-(self._fast_ma_period + 1) : -1])
        slow_ma_prev = self._calculate_ma(closes[-(self._slow_ma_period + 1) : -1])

        current_price = closes[-1]

        bullish_trend = fast_ma > slow_ma and fast_ma_prev <= slow_ma_prev
        bearish_trend = fast_ma < slow_ma and fast_ma_prev >= slow_ma_prev

        if bullish_trend:
            stop_loss = current_price * 0.95
            take_profit = current_price * 1.08
            return SignalResult(
                signal_type=SignalType.BUY,
                confidence=75.0,
                reason=f"Bullish MA crossover: fast({fast_ma:.2f}) > slow({slow_ma:.2f})",
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={"fast_ma": fast_ma, "slow_ma": slow_ma},
            )

        if bearish_trend:
            stop_loss = current_price * 1.05
            take_profit = current_price * 0.92
            return SignalResult(
                signal_type=SignalType.SELL,
                confidence=75.0,
                reason=f"Bearish MA crossover: fast({fast_ma:.2f}) < slow({slow_ma:.2f})",
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={"fast_ma": fast_ma, "slow_ma": slow_ma},
            )

        return None

    def _calculate_ma(self, prices: list[float]) -> float:
        if not prices:
            return 0.0
        return sum(prices) / len(prices)