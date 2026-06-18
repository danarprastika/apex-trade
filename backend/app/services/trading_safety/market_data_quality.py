from __future__ import annotations

import logging
from datetime import datetime, timezone, timedelta
from typing import Any

from sqlalchemy.orm import Session

from app.database.repositories.market_repository import AssetRepository, MarketPairRepository
from app.database.repositories.trading_safety_repository import MarketDataQualityEventRepository
from app.domain.exchange.models import UnifiedCandle, UnifiedTicker, UnifiedOrderBook

logger = logging.getLogger(__name__)


class MarketDataQualityEngine:
    STALE_THRESHOLD_SECONDS = 5
    PRICE_DEVIATION_THRESHOLD = 0.03

    def __init__(self, db: Session, event_bus: Any | None = None):
        self.db = db
        self.quality_events = MarketDataQualityEventRepository(db)
        self.market_pairs = MarketPairRepository(db)
        self.assets = AssetRepository(db)
        self.event_bus = event_bus

    def evaluate_candle_quality(self, candle: UnifiedCandle, market_pair_id: str, exchange_id: str) -> tuple[bool, float, list[str]]:
        issues = []
        quality_score = 1.0

        if self._is_candle_stale(candle):
            issues.append("stale_data")
            quality_score *= 0.5

        if self._has_invalid_prices(candle):
            issues.append("invalid_prices")
            quality_score *= 0.3

        if self._is_inverted_candle(candle):
            issues.append("inverted_candle")
            quality_score *= 0.4

        is_valid = quality_score >= 0.5
        self._log_quality_event(market_pair_id, exchange_id, "CANDLE", quality_score, issues, is_valid)
        return is_valid, quality_score, issues

    def evaluate_ticker_quality(self, ticker: UnifiedTicker, market_pair_id: str, exchange_id: str) -> tuple[bool, float, list[str]]:
        issues = []
        quality_score = 1.0

        if self._is_ticker_stale(ticker):
            issues.append("stale_data")
            quality_score *= 0.5

        if ticker.last_price is None or ticker.last_price <= 0:
            issues.append("missing_or_invalid_price")
            quality_score *= 0.2

        if self._price_deviation_anomaly(ticker):
            issues.append("price_anomaly")
            quality_score *= 0.6

        is_valid = quality_score >= 0.5
        self._log_quality_event(market_pair_id, exchange_id, "TICKER", quality_score, issues, is_valid)
        return is_valid, quality_score, issues

    def evaluate_order_book_quality(self, order_book: UnifiedOrderBook, market_pair_id: str, exchange_id: str) -> tuple[bool, float, list[str]]:
        issues = []
        quality_score = 1.0

        if self._is_order_book_stale(order_book):
            issues.append("stale_data")
            quality_score *= 0.5

        if not order_book.bids or not order_book.asks:
            issues.append("missing_depth")
            quality_score *= 0.7

        spread = self._calculate_spread(order_book)
        if spread and spread > 0.1:
            issues.append("wide_spread")
            quality_score *= 0.8

        is_valid = quality_score >= 0.4
        self._log_quality_event(market_pair_id, exchange_id, "ORDER_BOOK", quality_score, issues, is_valid)
        return is_valid, quality_score, issues

    def _is_candle_stale(self, candle: UnifiedCandle) -> bool:
        if candle.open_time is None:
            return True
        age = datetime.now(timezone.utc) - candle.open_time
        return age > timedelta(seconds=self.STALE_THRESHOLD_SECONDS)

    def _is_ticker_stale(self, ticker: UnifiedTicker) -> bool:
        if ticker.received_at is None:
            return True
        age = datetime.now(timezone.utc) - ticker.received_at
        return age > timedelta(seconds=self.STALE_THRESHOLD_SECONDS)

    def _is_order_book_stale(self, order_book: UnifiedOrderBook) -> bool:
        if order_book.captured_at is None:
            return True
        age = datetime.now(timezone.utc) - order_book.captured_at
        return age > timedelta(seconds=self.STALE_THRESHOLD_SECONDS)

    def _has_invalid_prices(self, candle: UnifiedCandle) -> bool:
        return candle.open < 0 or candle.high < 0 or candle.low < 0 or candle.close < 0 or candle.volume < 0

    def _is_inverted_candle(self, candle: UnifiedCandle) -> bool:
        return candle.high < candle.low

    def _calculate_spread(self, order_book: UnifiedOrderBook) -> float | None:
        if not order_book.bids or not order_book.asks:
            return None
        best_bid = order_book.bids[0].price
        best_ask = order_book.asks[0].price
        if best_bid <= 0 or best_ask <= 0:
            return None
        return (best_ask - best_bid) / best_bid

    def _price_deviation_anomaly(self, ticker: UnifiedTicker) -> bool:
        if ticker.high_24h is None or ticker.low_24h is None or ticker.last_price is None:
            return False
        if ticker.high_24h <= ticker.low_24h:
            return False
        price_range = ticker.high_24h - ticker.low_24h
        if price_range <= 0:
            return False
        deviation = abs(ticker.last_price - (ticker.high_24h + ticker.low_24h) / 2) / price_range
        return deviation > self.PRICE_DEVIATION_THRESHOLD

    def _log_quality_event(
        self,
        market_pair_id: str,
        exchange_id: str,
        data_type: str,
        quality_score: float,
        issues: list[str],
        is_valid: bool,
    ) -> None:
        self.quality_events.log_quality_check(
            market_pair_id=market_pair_id,
            exchange_id=exchange_id,
            data_type=data_type,
            quality_score=quality_score,
            issues={"detected": issues},
            is_valid=is_valid,
        )