from __future__ import annotations

from typing import Any

from app.domain.entities.strategy import StrategyType
from app.domain.strategies.base import StrategyPlugin
from app.domain.strategies.types import ConfigValidation, SignalResult, SignalType, StrategyMetadata


class ScalpingPlugin(StrategyPlugin):
    """Scalping strategy for high-frequency micro-opportunities."""

    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._spread_threshold: float = 0.001
        self._rsi_period: int = 9
        self._rsi_extreme: float = 25.0
        self._profit_target: float = 0.005
        self._max_position_time: int = 60

    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="Scalping",
            version="1.0.0",
            strategy_type=StrategyType.scalping,
            description="High-frequency strategy capturing small price movements with tight risk control",
            author="APEX Core",
            min_lookback_periods=20,
            supported_assets=["BTC", "ETH", "SOL", "SPX", "NDX"],
            supported_timeframes=["1m", "5m"],
        )

    def initialize(self, config: dict[str, Any]) -> None:
        self._config = config
        self._spread_threshold = config.get("spread_threshold", 0.001)
        self._rsi_period = config.get("rsi_period", 9)
        self._rsi_extreme = config.get("rsi_extreme", 25.0)
        self._profit_target = config.get("profit_target", 0.005)
        self._max_position_time = config.get("max_position_time", 60)

    def validate_config(self, config: dict[str, Any]) -> ConfigValidation:
        errors = []
        if "spread_threshold" in config:
            if not isinstance(config["spread_threshold"], (int, float)) or config["spread_threshold"] <= 0:
                errors.append("spread_threshold must be a positive number")
        if "rsi_period" in config:
            if not isinstance(config["rsi_period"], int) or config["rsi_period"] < 2:
                errors.append("rsi_period must be a positive integer >= 2")
        if "rsi_extreme" in config:
            if not isinstance(config["rsi_extreme"], (int, float)) or not 0 < config["rsi_extreme"] < 50:
                errors.append("rsi_extreme must be between 0 and 50")
        if "profit_target" in config:
            if not isinstance(config["profit_target"], (int, float)) or config["profit_target"] <= 0:
                errors.append("profit_target must be a positive number")
        return ConfigValidation(valid=len(errors) == 0, errors=errors)

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "spread_threshold": {
                    "type": "number",
                    "minimum": 0.0001,
                    "maximum": 0.01,
                    "default": 0.001,
                    "description": "Maximum spread for valid scalping opportunity",
                },
                "rsi_period": {
                    "type": "integer",
                    "minimum": 2,
                    "maximum": 20,
                    "default": 9,
                    "description": "RSI period for momentum detection",
                },
                "rsi_extreme": {
                    "type": "number",
                    "minimum": 5,
                    "maximum": 40,
                    "default": 25.0,
                    "description": "RSI extreme threshold for entry",
                },
                "profit_target": {
                    "type": "number",
                    "minimum": 0.001,
                    "maximum": 0.02,
                    "default": 0.005,
                    "description": "Target profit percentage per trade",
                },
                "max_position_time": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 300,
                    "default": 60,
                    "description": "Maximum position holding time in seconds",
                },
            },
            "required": [],
        }

    def analyze(self, market_data: dict[str, Any]) -> SignalResult | None:
        candles = market_data.get("candles", [])
        orderbook = market_data.get("orderbook", {})

        if len(candles) < self._rsi_period + 3:
            return None

        closes = [c["close"] for c in candles[-(self._rsi_period + 3) :]]
        current_price = closes[-1]
        rsi = self._calculate_rsi(closes)

        bid = orderbook.get("bid", 0)
        ask = orderbook.get("ask", 0)
        if bid > 0 and ask > 0:
            spread = (ask - bid) / bid
            if spread > self._spread_threshold:
                return None

        if rsi < self._rsi_extreme:
            stop_loss = current_price * (1 - self._profit_target * 2)
            take_profit = current_price * (1 + self._profit_target)
            return SignalResult(
                signal_type=SignalType.BUY,
                confidence=65.0,
                reason=f"Scalping buy: RSI({rsi:.1f}) oversold, tight spread",
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={"rsi": rsi, "spread": spread if bid > 0 else None},
            )

        if rsi > 100 - self._rsi_extreme:
            stop_loss = current_price * (1 + self._profit_target * 2)
            take_profit = current_price * (1 - self._profit_target)
            return SignalResult(
                signal_type=SignalType.SELL,
                confidence=65.0,
                reason=f"Scalping sell: RSI({rsi:.1f}) overbought, tight spread",
                entry_price=current_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                metadata={"rsi": rsi, "spread": spread if bid > 0 else None},
            )

        return None

    def _calculate_rsi(self, prices: list[float]) -> float:
        if len(prices) < self._rsi_period + 1:
            return 50.0

        deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
        gains = [d if d > 0 else 0 for d in deltas[-self._rsi_period :]]
        losses = [-d if d < 0 else 0 for d in deltas[-self._rsi_period :]]

        avg_gain = sum(gains) / self._rsi_period
        avg_loss = sum(losses) / self._rsi_period

        if avg_loss == 0:
            return 100.0

        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))