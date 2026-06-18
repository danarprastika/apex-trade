from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.domain.exchange.models import UnifiedCandle
from app.services.trading_safety.market_data_quality import MarketDataQualityEngine


def test_market_data_quality_valid_candle():
    engine = None
    from unittest.mock import MagicMock
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()

    engine = MarketDataQualityEngine(db)

    candle = UnifiedCandle(
        exchange_id="binance",
        exchange_name="Binance",
        source_symbol="BTCUSDT",
        normalized_symbol="BTC/USDT",
        base_asset="BTC",
        quote_asset="USDT",
        timeframe="1h",
        open_time=datetime.now(UTC) - timedelta(seconds=1),
        close_time=datetime.now(UTC),
        open=50000.0,
        high=51000.0,
        low=49500.0,
        close=50500.0,
        volume=100.0,
    )

    is_valid, score, issues = engine.evaluate_candle_quality(candle, "market-pair-123", "binance")
    assert is_valid is True
    assert score >= 0.5
    assert issues == []


def test_market_data_quality_stale_candle():
    from unittest.mock import MagicMock
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()

    engine = MarketDataQualityEngine(db)

    stale_candle = UnifiedCandle(
        exchange_id="binance",
        exchange_name="Binance",
        source_symbol="BTCUSDT",
        normalized_symbol="BTC/USDT",
        base_asset="BTC",
        quote_asset="USDT",
        timeframe="1h",
        open_time=datetime.now(UTC) - timedelta(seconds=10),
        close_time=datetime.now(UTC) - timedelta(seconds=10),
        open=50000.0,
        high=51000.0,
        low=49500.0,
        close=50500.0,
        volume=100.0,
    )

    is_valid, score, issues = engine.evaluate_candle_quality(stale_candle, "market-pair-123", "binance")
    assert is_valid is True
    assert "stale_data" in issues


def test_market_data_quality_invalid_prices():
    from unittest.mock import MagicMock
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()

    engine = MarketDataQualityEngine(db)

    invalid_candle = UnifiedCandle(
        exchange_id="binance",
        exchange_name="Binance",
        source_symbol="BTCUSDT",
        normalized_symbol="BTC/USDT",
        base_asset="BTC",
        quote_asset="USDT",
        timeframe="1h",
        open_time=datetime.now(UTC) - timedelta(seconds=1),
        close_time=datetime.now(UTC),
        open=-50000.0,
        high=51000.0,
        low=49500.0,
        close=50500.0,
        volume=100.0,
    )

    is_valid, score, issues = engine.evaluate_candle_quality(invalid_candle, "market-pair-123", "binance")
    assert is_valid is False
    assert "invalid_prices" in issues


def test_market_data_quality_inverted_candle():
    from unittest.mock import MagicMock
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()

    engine = MarketDataQualityEngine(db)

    inverted_candle = UnifiedCandle(
        exchange_id="binance",
        exchange_name="Binance",
        source_symbol="BTCUSDT",
        normalized_symbol="BTC/USDT",
        base_asset="BTC",
        quote_asset="USDT",
        timeframe="1h",
        open_time=datetime.now(UTC) - timedelta(seconds=1),
        close_time=datetime.now(UTC),
        open=50000.0,
        high=49000.0,
        low=51000.0,
        close=50500.0,
        volume=100.0,
    )

    is_valid, score, issues = engine.evaluate_candle_quality(inverted_candle, "market-pair-123", "binance")
    assert is_valid is False
    assert "inverted_candle" in issues
