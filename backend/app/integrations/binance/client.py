from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import ccxt
import structlog

logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class CandlePayload:
    open_time: datetime
    close_time: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


class BinanceClient:
    allowed_timeframes = {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d", "1w", "1M"}

    def __init__(self, api_key: str | None = None, api_secret: str | None = None, testnet: bool = True) -> None:
        options = {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {"adjustForTimeDifference": True},
        }
        if testnet:
            options["urls"] = {"api": {"public": "https://testnet.binance.vision/api/v3", "private": "https://testnet.binance.vision/api/v3"}}
        self.exchange = ccxt.binance(options)

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100) -> list[CandlePayload]:
        normalized_symbol = self._normalize_symbol(symbol)
        normalized_timeframe = self._normalize_timeframe(timeframe)
        normalized_limit = self._normalize_limit(limit)

        try:
            raw_candles = self.exchange.fetch_ohlcv(normalized_symbol, timeframe=normalized_timeframe, limit=normalized_limit)
        except Exception as exc:
            logger.exception("Binance OHLCV fetch failed", symbol=normalized_symbol, timeframe=normalized_timeframe)
            raise

        return [self._parse_candle(candle) for candle in raw_candles]

    def fetch_ticker(self, symbol: str) -> dict[str, Any]:
        normalized_symbol = self._normalize_symbol(symbol)
        try:
            return self.exchange.fetch_ticker(normalized_symbol)
        except Exception as exc:
            logger.exception("Binance ticker fetch failed", symbol=normalized_symbol)
            raise

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = symbol.upper().replace("/", "").replace("-", "").replace("_", "")
        if len(normalized) < 4 or any(char.isdigit() for char in normalized):
            raise ValueError("Invalid Binance symbol")
        return normalized

    @classmethod
    def _normalize_timeframe(cls, timeframe: str) -> str:
        normalized = timeframe.lower()
        if normalized not in cls.allowed_timeframes:
            raise ValueError(f"Unsupported Binance timeframe: {timeframe}")
        return normalized

    @staticmethod
    def _normalize_limit(limit: int) -> int:
        if limit < 1:
            raise ValueError("limit must be greater than zero")
        return min(limit, 1000)

    @staticmethod
    def _parse_candle(candle: list[float | int]) -> CandlePayload:
        if len(candle) < 6:
            raise ValueError("Invalid OHLCV payload")

        open_ms, open_value, high_value, low_value, close_value, volume_value = candle[:6]
        open_float = float(open_value)
        high_float = float(high_value)
        low_float = float(low_value)
        close_float = float(close_value)
        volume_float = float(volume_value)

        if high_float < max(open_float, close_float, low_float) or low_float > min(open_float, close_float, high_float):
            raise ValueError("Invalid OHLC values")
        if volume_float < 0:
            raise ValueError("Invalid candle volume")

        return CandlePayload(
            open_time=datetime.fromtimestamp(int(open_ms) / 1000, tz=timezone.utc),
            close_time=datetime.fromtimestamp((int(open_ms) + 60_000) / 1000, tz=timezone.utc),
            open=open_float,
            high=high_float,
            low=low_float,
            close=close_float,
            volume=volume_float,
        )
