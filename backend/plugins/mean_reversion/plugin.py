from __future__ import annotations

from typing import Any

from app.domain.entities.strategy import StrategyType
from app.domain.strategies.base import StrategyPlugin
from app.domain.strategies.types import ConfigValidation, SignalResult, SignalType, StrategyMetadata


class MeanReversionPlugin(StrategyPlugin):
    """Mean reversion strategy based on Bollinger Bands and RSI."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._bb_period: int = 20
        self._bb_std_dev: float = 2.0
        self._rsi_period: int = 14
        self._rsi_overbought: float = 70.0
        self._rsi_oversold: float = 30.0

    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="Mean Reversion",
            version="1.0.0",
            strategy_type=StrategyType.mean_reversion,
            description="Capitalizes on price reverting to mean values using Bollinger Bands and RSI",
            author="APEX Core",
            min_lookback_periods=50,
            supported_assets=["BTC", "ETH", "SOL", "SPX", "NDX"],
            supported_timeframes=["5m", "15m", "1h", "4h", "1d"],
        )

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._bb_period = config.get("bb_period", 20)
        self._bb_std_dev = config.get("bb_std_dev", 2.0)
        self._rsi_period = config.get("rsi_period", 14)
        self._rsi_overbought = config.get("rsi_overbought", 70.0)
        self._rsi_oversold = config.get("rsi_oversold", 30.0)

    def validate_config(self, config: dict[str, Any]) -> ConfigValidation:
        errors = []
        if "bb_period" in config:
            if not isinstance(config["bb_period"], int) or config["bb_period"] < 1:
                errors.append("bb_period must be a positive integer")
        if "bb_std_dev" in config:
            if not isinstance(config["bb_std_dev"], (int, float)) or config["bb_std_dev"] <= 0:
                errors.append("bb_std_dev must be a positive number")
        if "rsi_overbought" in config:
            if not isinstance(config["rsi_overbought"], (int, float)):
                errors.append("rsi_overbought must be a number")
        if "rsi_oversold" in config:
            if not isinstance(config["rsi_oversold"], (int, float)):
                errors.append("rsi_oversold must be a number")
        if (
            "rsi_oversold" in config
            and "rsi_overbought" in config
            and config["rsi_oversold"] >= config["rsi_overbought"]
        ):
            errors.append("rsi_oversold must be less than rsi_overbought")
        return ConfigValidation(valid=len(errors) == 0, errors=errors)

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "bb_period": {
                    "type": "integer",
                    "minimum": 5,
                    "maximum": 100,
                    "default": 20,
                    "description": "Bollinger Bands period",
                },
                "bb_std_dev": {
                    "type": "number",
                    "minimum": 1.0,
                    "maximum": 5.0,
                    "default": 2.0,
                    "description": "Standard deviation multiplier for bands",
                },
                "rsi_period": {
                    "type": "integer",
                    "minimum": 2,
                    "maximum": 50,
                    "default": 14,
                    "description": "RSI calculation period",
                },
                "rsi_overbought": {
                    "type": "number",
                    "minimum": 50,
                    "maximum": 100,
                    "default": 70.0,
                    "description": "RSI overbought threshold",
                },
                "rsi_oversold": {
                    "type": "number",
                    "minimum": 0,
                    "maximum": 50,
                    "default": 30.0,
                    "description": "RSI oversold threshold",
                },
            },
            "required": [],
        }

    def analyze(self, market_data: dict[str, Any]) -> SignalResult | None:
        candles = market_data.get("candles", [])
        if len(candles) < self._bb_period + self._rsi_period:
            return None

        closes = [c["close"] for c in candles]
        current_price = closes[-1]
        rsi = self._calculate_rsi(closes)

        sma = sum(closes[-self._bb_period:]) / self._bb_period
        std_dev = self._calculate_std_dev(closes[-self._bb_period:], sma)
        upper_band = sma + (self._bb_std_dev * std_dev)
        lower_band = sma - (self._bb_std_dev * std_dev)

        if rsi < self._rsi_oversold and current_price <= lower_band * 1.02:
            stop_loss = sma
            take_profit = sma + (sma - lower_band)
            return SignalResult(
                signal_type=SignalType.BUY,
                confidence=80.0,
                reason=f"Oversold RSI({rsi:.1f}) with price at lower band({current_price:.2f} < {lower_band:.2f})",
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={"rsi": rsi, "lower_band": lower_band, "sma": sma},
            )

        if rsi > self._rsi_overbought and current_price >= upper_band * 0.98:
            stop_loss = sma
            take_profit = sma - (upper_band - sma)
            return SignalResult(
                signal_type=SignalType.SELL,
                confidence=80.0,
                reason=f"Overbought RSI({rsi:.1f}) with price at upper band({current_price:.2f} > {upper_band:.2f})",
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={"rsi": rsi, "upper_band": upper_band, "sma": sma},
            )

        return None

    def _calculate_rsi(self, prices: list[float]) -> float:
        if len(prices) < self._rsi_period + 1:
            return 50.0

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices[-self._rsi_period - 1 :]))]
        gains = [d if d > 0 else 0 for d in deltas]
        losses = [-d if d < 0 else 0 for d in deltas]

        avg_gain = sum(gains[-self._rsi_period:]) / self._rsi_period
        avg_loss = sum(losses[-self._rsi_period:]) / self._rsi_period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def _calculate_std_dev(self, values: list[float], mean: float) -> float:
        if not values:
            return 0.0
        variance = sum((v - mean) ** 2 for v in values) / len(values)
        return variance**0.5