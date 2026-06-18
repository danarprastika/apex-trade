from __future__ import annotations

from app.domain.exchange.value_objects import ExchangeErrorCategory
from app.integrations.exchanges.errors import ExchangeRateLimitError, ExchangeValidationError
from app.integrations.exchanges.errors.mapper import ExchangeErrorMapper
from app.integrations.exchanges.rate_limit import ExchangeRateLimitManager, RateLimitPolicy
from app.integrations.exchanges.registry import ExchangeAdapterRegistry, ExchangeCapabilityCatalog
from app.integrations.exchanges.retry import RetryManager, RetryPolicy


def test_exchange_capability_catalog_contains_future_exchanges():
    catalog = ExchangeCapabilityCatalog()

    assert catalog.get("binance") is not None
    assert catalog.get("bybit") is not None
    assert catalog.get("okx") is not None
    assert catalog.get("kucoin") is not None
    assert catalog.get("kraken") is not None
    assert catalog.get("interactive_brokers") is not None


def test_exchange_adapter_registry_resolves_binance_by_name_and_type():
    from app.integrations.exchanges.binance import BinanceAdapter

    registry = ExchangeAdapterRegistry()
    adapter = BinanceAdapter(testnet=True)
    registry.register("binance", adapter)

    assert registry.get("Binance") is adapter
    assert registry.get("binance") is adapter
    assert registry.get("SPOT") is adapter


def test_retry_manager_retries_rate_limit_but_not_validation():
    manager = RetryManager(RetryPolicy(max_attempts=2, base_delay_seconds=0.1))

    rate_limit = ExchangeRateLimitError("rate limit")
    validation = ExchangeValidationError("invalid symbol")

    assert manager.should_retry(rate_limit, attempt=1).should_retry is True
    assert manager.should_retry(validation, attempt=1).should_retry is False


def test_rate_limit_manager_blocks_after_capacity():
    manager = ExchangeRateLimitManager({"fetch_candles": RateLimitPolicy(calls=1, period_seconds=60)})

    assert manager.acquire("fetch_candles") is True
    assert manager.acquire("fetch_candles") is False


def test_error_mapper_classifies_rate_limit_and_validation_errors():
    mapper = ExchangeErrorMapper()

    rate_limit = mapper.map_error(RuntimeError("rate limit exceeded"))
    validation = mapper.map_error(RuntimeError("invalid symbol BTCUSDT"))

    assert rate_limit.category == ExchangeErrorCategory.RATE_LIMIT
    assert validation.category == ExchangeErrorCategory.VALIDATION


def test_binance_adapter_normalizes_candles():
    from app.integrations.exchanges.binance import BinanceAdapter

    class FakeClient:
        def fetch_ohlcv(self, symbol, timeframe="1h", limit=100):
            return [[1700000000000, 1, 2, 0.5, 1.5, 10]]

        def _normalize_symbol(self, symbol):
            return symbol.upper().replace("/", "")

    adapter = BinanceAdapter(testnet=True, client=FakeClient())
    context = adapter._context("fetch_candles", symbol="BTC/USDT")

    candles = adapter.fetch_candles("BTC/USDT", timeframe="1h", limit=1, context=context)

    assert len(candles) == 1
    assert candles[0].normalized_symbol == "BTCUSDT"
    assert candles[0].open == 1
    assert candles[0].close == 1.5
    assert candles[0].volume == 10
    assert candles[0].base_asset == "BTC"
    assert candles[0].quote_asset == "USDT"


def test_binance_adapter_ticker_normalizes_raw_ccxt_payload():
    from app.integrations.exchanges.binance import BinanceAdapter

    class FakeClient:
        def fetch_ticker(self, symbol):
            return {
                "last": "100.5",
                "bid": "100.0",
                "ask": "101.0",
                "high": "105.0",
                "low": "99.0",
                "baseVolume": "10",
                "quoteVolume": "1000",
                "timestamp": 1700000000000,
            }

        def _normalize_symbol(self, symbol):
            return symbol.upper().replace("/", "")

    adapter = BinanceAdapter(testnet=True, client=FakeClient())
    ticker = adapter.fetch_ticker("BTC/USDT", context=adapter._context("fetch_ticker", symbol="BTC/USDT"))

    assert ticker.normalized_symbol == "BTCUSDT"
    assert ticker.last_price == 100.5
    assert ticker.bid_price == 100.0
    assert ticker.ask_price == 101.0
    assert ticker.volume_24h == 10
