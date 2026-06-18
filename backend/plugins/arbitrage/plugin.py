from __future__ import annotations

from typing import Any

from app.domain.entities.strategy import StrategyType
from app.domain.strategies.base import StrategyPlugin
from app.domain.strategies.types import ConfigValidation, SignalResult, SignalType, StrategyMetadata


class ArbitragePlugin(StrategyPlugin):
    def __init__(self) -> None:
        self._config: dict[str, Any] = {}
        self._maker_fee: float = 0.001
        self._taker_fee: float = 0.001
        self._min_profit_pct: float = 0.002
        self._max_slippage_pct: float = 0.0005
        self._min_spread_pct: float = 0.001

    @property
    def metadata(self) -> StrategyMetadata:
        return StrategyMetadata(
            name="Arbitrage",
            version="1.0.0",
            strategy_type=StrategyType.arbitrage,
            description="Fee-aware cross-exchange arbitrage detector",
            author="APEX Core",
            min_lookback_periods=1,
            supported_assets=["BTC", "ETH", "SOL", "SPX", "NDX"],
            supported_timeframes=["1m", "5m", "15m"],
        )

    def initialize(self, config: dict[str, Any]) -> None:
        validation = self.validate_config(config)
        if not validation.valid:
            raise ValueError(validation.errors)
        self._config = config
        self._maker_fee = float(config.get("maker_fee", self._maker_fee))
        self._taker_fee = float(config.get("taker_fee", self._taker_fee))
        self._min_profit_pct = float(config.get("min_profit_pct", self._min_profit_pct))
        self._max_slippage_pct = float(config.get("max_slippage_pct", self._max_slippage_pct))
        self._min_spread_pct = float(config.get("min_spread_pct", self._min_spread_pct))

    def validate_config(self, config: dict[str, Any]) -> ConfigValidation:
        errors: list[str] = []
        for field_name in ("maker_fee", "taker_fee", "min_profit_pct", "max_slippage_pct", "min_spread_pct"):
            if field_name in config:
                value = config[field_name]
                if not isinstance(value, (int, float)) or value < 0:
                    errors.append(f"{field_name} must be a non-negative number")
        if "min_profit_pct" in config and "min_spread_pct" in config and config["min_profit_pct"] < config["min_spread_pct"]:
            errors.append("min_profit_pct must be greater than or equal to min_spread_pct")
        return ConfigValidation(valid=len(errors) == 0, errors=errors)

    def get_parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "maker_fee": {"type": "number", "minimum": 0, "maximum": 0.01, "default": 0.001},
                "taker_fee": {"type": "number", "minimum": 0, "maximum": 0.01, "default": 0.001},
                "min_profit_pct": {"type": "number", "minimum": 0, "maximum": 0.1, "default": 0.002},
                "max_slippage_pct": {"type": "number", "minimum": 0, "maximum": 0.01, "default": 0.0005},
                "min_spread_pct": {"type": "number", "minimum": 0, "maximum": 0.1, "default": 0.001},
            },
            "required": [],
        }

    def analyze(self, market_data: dict[str, Any]) -> SignalResult | None:
        quotes = market_data.get("quotes")
        if not isinstance(quotes, list) or len(quotes) < 2:
            return None

        normalized_quotes = self._normalize_quotes(quotes)
        if len(normalized_quotes) < 2:
            return None

        buy_quote = min(normalized_quotes, key=lambda quote: quote["ask"])
        sell_quote = max(normalized_quotes, key=lambda quote: quote["bid"])
        if buy_quote["exchange"] == sell_quote["exchange"]:
            return None
        if buy_quote["ask"] <= 0 or sell_quote["bid"] <= 0:
            return None

        gross_spread = sell_quote["bid"] - buy_quote["ask"]
        if gross_spread <= 0:
            return None
        gross_profit_pct = gross_spread / buy_quote["ask"]
        if gross_profit_pct < self._min_spread_pct:
            return None

        fees = buy_quote.get("taker_fee", self._taker_fee) + sell_quote.get("maker_fee", self._maker_fee)
        slippage = self._max_slippage_pct
        net_profit_pct = gross_profit_pct - fees - slippage
        if net_profit_pct < self._min_profit_pct:
            return None

        estimated_gross_profit = gross_spread
        estimated_fees = (buy_quote["ask"] * buy_quote.get("taker_fee", self._taker_fee)) + (
            sell_quote["bid"] * sell_quote.get("maker_fee", self._maker_fee)
        )
        estimated_net_profit = estimated_gross_profit - estimated_fees - (buy_quote["ask"] * slippage)

        return SignalResult(
            signal_type=SignalType.BUY,
            confidence=min(99.0, 60.0 + net_profit_pct * 1000),
            reason=(
                f"Arbitrage opportunity: buy {buy_quote['exchange']} at {buy_quote['ask']} "
                f"sell {sell_quote['exchange']} at {sell_quote['bid']}"
            ),
            entry_price=buy_quote["ask"],
            stop_loss=buy_quote["ask"],
            take_profit=sell_quote["bid"],
            metadata={
                "buy_exchange": buy_quote["exchange"],
                "sell_exchange": sell_quote["exchange"],
                "buy_price": buy_quote["ask"],
                "sell_price": sell_quote["bid"],
                "gross_spread": gross_spread,
                "gross_profit_pct": gross_profit_pct,
                "fees": fees,
                "slippage_pct": slippage,
                "net_profit_pct": net_profit_pct,
                "estimated_net_profit": estimated_net_profit,
                "legs": [
                    {"side": "BUY", "exchange": buy_quote["exchange"], "price": buy_quote["ask"]},
                    {"side": "SELL", "exchange": sell_quote["exchange"], "price": sell_quote["bid"]},
                ],
            },
        )

    def _normalize_quotes(self, quotes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for quote in quotes:
            if not isinstance(quote, dict):
                continue
            exchange = quote.get("exchange")
            bid = quote.get("bid")
            ask = quote.get("ask")
            if not isinstance(exchange, str) or not exchange:
                continue
            if not self._is_positive_number(bid) or not self._is_positive_number(ask):
                continue
            normalized_quote = {
                "exchange": exchange,
                "bid": float(bid),
                "ask": float(ask),
                "maker_fee": float(quote.get("maker_fee", self._maker_fee)),
                "taker_fee": float(quote.get("taker_fee", self._taker_fee)),
            }
            normalized.append(normalized_quote)
        return normalized

    def _is_positive_number(self, value: Any) -> bool:
        return isinstance(value, (int, float)) and value > 0
