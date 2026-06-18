from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.domain.exchange.models import (
    ExchangeCapability,
    ExchangeHealth,
    ExchangeOperationContext,
    UnifiedBalance,
    UnifiedCandle,
    UnifiedOrder,
    UnifiedTicker,
)
from app.integrations.binance.client import BinanceClient, CandlePayload
from app.integrations.exchanges.base import BaseExchangeAdapter
from app.integrations.exchanges.rate_limit import RateLimitPolicy


class BinanceAdapter(BaseExchangeAdapter):
    exchange_id = "binance"
    exchange_name = "Binance"
    capabilities = ExchangeCapability(
        exchange_id="binance",
        exchange_name="Binance",
        asset_classes=("CRYPTO",),
        spot=True,
        order_book=True,
        submit_order=False,
        cancel_order=False,
        modify_order=False,
        fetch_order=False,
        fetch_positions=False,
        fetch_balances=True,
        supported_order_types=("MARKET", "LIMIT"),
        supported_time_in_force=("GTC",),
    )
    rate_limit_policy = {
        "fetch_candles": RateLimitPolicy(calls=10, period_seconds=1),
        "fetch_ticker": RateLimitPolicy(calls=20, period_seconds=1),
    }

    def __init__(self, api_key: str | None = None, api_secret: str | None = None, testnet: bool = True, client: BinanceClient | None = None) -> None:
        super().__init__(api_key=api_key, api_secret=api_secret, testnet=testnet)
        self.client = client or BinanceClient(api_key=api_key, api_secret=api_secret, testnet=testnet)

    def normalize_symbol(self, symbol: str) -> str:
        return self.client._normalize_symbol(symbol)

    def fetch_candles(self, symbol: str, timeframe: str, limit: int, context: ExchangeOperationContext) -> list[UnifiedCandle]:
        if not self.rate_limit_manager.acquire("fetch_candles"):
            raise self.error_mapper.map_error(RuntimeError("Binance candle rate limit exceeded"))

        raw_candles = self.client.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        self.last_health = ExchangeHealth(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            available=True,
            last_checked_at=datetime.now(timezone.utc),
        )
        return [self._to_unified_candle(candle, symbol, timeframe) for candle in raw_candles]

    def fetch_ticker(self, symbol: str, context: ExchangeOperationContext) -> UnifiedTicker:
        if not self.rate_limit_manager.acquire("fetch_ticker"):
            raise self.error_mapper.map_error(RuntimeError("Binance ticker rate limit exceeded"))

        raw_ticker = self.client.fetch_ticker(symbol=symbol)
        self.last_health = ExchangeHealth(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            available=True,
            last_checked_at=datetime.now(timezone.utc),
        )
        normalized_symbol = self.normalize_symbol(symbol)
        return UnifiedTicker(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            source_symbol=symbol,
            normalized_symbol=normalized_symbol,
            last_price=self._safe_float(raw_ticker.get("last")),
            bid_price=self._safe_float(raw_ticker.get("bid")),
            ask_price=self._safe_float(raw_ticker.get("ask")),
            high_24h=self._safe_float(raw_ticker.get("high")),
            low_24h=self._safe_float(raw_ticker.get("low")),
            volume_24h=self._safe_float(raw_ticker.get("baseVolume")),
            quote_volume_24h=self._safe_float(raw_ticker.get("quoteVolume")),
            source_timestamp=self._datetime_from_value(raw_ticker.get("timestamp")),
            received_at=datetime.now(timezone.utc),
        )

    def _to_unified_candle(self, candle: CandlePayload | list[float | int], symbol: str, timeframe: str) -> UnifiedCandle:
        normalized_symbol = self.normalize_symbol(symbol)
        open_time = self._candle_open_time(candle)
        close_time = self._candle_close_time(candle)
        return UnifiedCandle(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            source_symbol=symbol,
            normalized_symbol=normalized_symbol,
            base_asset=normalized_symbol[:-4],
            quote_asset=normalized_symbol[-4:],
            timeframe=timeframe,
            open_time=open_time,
            close_time=close_time,
            open=self._candle_value(candle, 1),
            high=self._candle_value(candle, 2),
            low=self._candle_value(candle, 3),
            close=self._candle_value(candle, 4),
            volume=self._candle_value(candle, 5),
            source_timestamp=open_time,
            received_at=datetime.now(timezone.utc),
        )

    @staticmethod
    def _candle_value(candle: CandlePayload | list[float | int], index: int) -> float:
        if isinstance(candle, CandlePayload):
            return float(getattr(candle, ["open", "high", "low", "close", "volume"][index - 1]))
        return float(candle[index])

    @staticmethod
    def _candle_open_time(candle: CandlePayload | list[float | int]) -> datetime:
        if isinstance(candle, CandlePayload):
            return candle.open_time
        return datetime.fromtimestamp(int(candle[0]) / 1000, tz=timezone.utc)

    @staticmethod
    def _candle_close_time(candle: CandlePayload | list[float | int]) -> datetime:
        if isinstance(candle, CandlePayload):
            return candle.close_time
        return datetime.fromtimestamp((int(candle[0]) + 60_000) / 1000, tz=timezone.utc)

    @staticmethod
    def _safe_float(value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _datetime_from_value(value: object) -> datetime | None:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        return None

    def fetch_balances(self, context: ExchangeOperationContext) -> list[UnifiedBalance]:
        if not self.rate_limit_manager.acquire("fetch_balances"):
            raise self.error_mapper.map_error(RuntimeError("Binance balance rate limit exceeded"))

        raw_balance = self.client.fetch_balance()
        self.last_health = ExchangeHealth(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            available=True,
            last_checked_at=datetime.now(timezone.utc),
        )
        return self._to_unified_balances(raw_balance, context)

    def _to_unified_balances(self, raw_balance: dict[str, Any], context: ExchangeOperationContext) -> list[UnifiedBalance]:
        total = raw_balance.get("total") or {}
        free = raw_balance.get("free") or {}
        used = raw_balance.get("used") or {}
        currencies = sorted(set(total) | set(free) | set(used))

        balances = []
        for currency in currencies:
            if currency == "info":
                continue
            normalized_currency = currency.upper()
            balances.append(
                UnifiedBalance(
                    exchange_id=self.exchange_id,
                    exchange_name=self.exchange_name,
                    user_id=context.user_id or "",
                    account_id=context.account_id or "",
                    currency=normalized_currency,
                    free=float(free.get(currency, 0)),
                    used=float(used.get(currency, 0)),
                    total=float(total.get(currency, 0)),
                    available=float(free.get(currency, 0)),
                    captured_at=datetime.now(timezone.utc),
                )
            )
        return balances
