from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import ccxt
import structlog

from app.domain.exchange.models import (
    ExchangeCapability,
    ExchangeOperationContext,
    OrderBookLevel,
    UnifiedBalance,
    UnifiedCandle,
    UnifiedOrder,
    UnifiedOrderBook,
    UnifiedPosition,
    UnifiedTicker,
)
from app.integrations.exchanges.base import BaseExchangeAdapter
from app.integrations.exchanges.rate_limit import RateLimitPolicy

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
    quote_volume: float | None = None


class BybitClient:
    allowed_timeframes = {"1m", "3m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "12h", "1d", "1w", "1M"}

    def __init__(self, api_key: str | None = None, api_secret: str | None = None, testnet: bool = False) -> None:
        options = {
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True,
            "options": {
                "adjustForTimeDifference": True,
                "defaultType": "spot",
            },
        }
        if testnet:
            options["urls"] = {
                "api": {
                    "public": "https://api-testnet.bybit.com",
                    "private": "https://api-testnet.bybit.com",
                }
            }
        self.exchange = ccxt.bybit(options)

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 100, params: dict[str, Any] | None = None) -> list[CandlePayload]:
        normalized_symbol = self._normalize_symbol(symbol)
        normalized_timeframe = self._normalize_timeframe(timeframe)
        normalized_limit = self._normalize_limit(limit)
        ccxt_symbol = self._ccxt_symbol(normalized_symbol, params)
        try:
            raw_candles = self.exchange.fetch_ohlcv(
                ccxt_symbol,
                timeframe=normalized_timeframe,
                limit=normalized_limit,
                params=params or {},
            )
        except Exception as exc:
            logger.exception("Bybit OHLCV fetch failed", symbol=ccxt_symbol, timeframe=normalized_timeframe)
            raise
        return [self._parse_candle(candle) for candle in raw_candles]

    def fetch_ticker(self, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        ccxt_symbol = self._ccxt_symbol(symbol, params)
        try:
            return self.exchange.fetch_ticker(ccxt_symbol, params=params or {})
        except Exception as exc:
            logger.exception("Bybit ticker fetch failed", symbol=ccxt_symbol)
            raise

    def fetch_order_book(self, symbol: str, limit: int = 20, params: dict[str, Any] | None = None) -> dict[str, Any]:
        ccxt_symbol = self._ccxt_symbol(symbol, params)
        normalized_limit = self._normalize_order_book_limit(limit)
        try:
            return self.exchange.fetch_order_book(ccxt_symbol, limit=normalized_limit, params=params or {})
        except Exception as exc:
            logger.exception("Bybit order book fetch failed", symbol=ccxt_symbol)
            raise

    def fetch_balance(self, params: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            return self.exchange.fetch_balance(params=params or {})
        except Exception as exc:
            logger.exception("Bybit balance fetch failed")
            raise

    def fetch_positions(self, symbol: str | None = None, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        params = dict(params or {})
        params.setdefault("category", "linear")
        ccxt_symbol = self._ccxt_symbol(symbol, params) if symbol else None
        try:
            symbols = [ccxt_symbol] if ccxt_symbol else None
            return self.exchange.fetch_positions(symbols, params=params)
        except Exception as exc:
            logger.exception("Bybit position fetch failed", symbol=ccxt_symbol)
            raise

    def create_order(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: float,
        price: float | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ccxt_symbol = self._ccxt_symbol(symbol, params)
        try:
            return self.exchange.create_order(
                ccxt_symbol,
                type=type,
                side=side,
                amount=quantity,
                price=price,
                params=params or {},
            )
        except Exception as exc:
            logger.exception("Bybit order submit failed", symbol=ccxt_symbol, side=side, type=type)
            raise

    def cancel_order(self, order_id: str, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        ccxt_symbol = self._ccxt_symbol(symbol, params)
        try:
            return self.exchange.cancel_order(order_id, ccxt_symbol, params=params or {})
        except Exception as exc:
            logger.exception("Bybit order cancel failed", order_id=order_id, symbol=ccxt_symbol)
            raise

    def fetch_order(self, order_id: str, symbol: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        ccxt_symbol = self._ccxt_symbol(symbol, params)
        try:
            return self.exchange.fetch_order(order_id, ccxt_symbol, params=params or {})
        except Exception as exc:
            logger.exception("Bybit order fetch failed", order_id=order_id, symbol=ccxt_symbol)
            raise

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        if not symbol:
            raise ValueError("symbol is required")
        normalized = str(symbol).upper().strip().replace(" ", "").replace("_", "")
        if "/" in normalized:
            base, quote = normalized.split("/", 1)
            normalized = base.replace("-", "") + quote.split(":")[0].replace("-", "")
        elif ":" in normalized:
            left, right = normalized.split(":", 1)
            normalized = left.replace("/", "").replace("-", "") + right.replace("/", "").replace("-", "")
        else:
            normalized = normalized.replace("-", "")
        if len(normalized) < 4:
            raise ValueError("Invalid Bybit symbol")
        return normalized

    @staticmethod
    def _normalize_timeframe(timeframe: str) -> str:
        normalized = timeframe.strip()
        if normalized in BybitClient.allowed_timeframes:
            return normalized
        normalized = normalized.lower()
        if normalized in BybitClient.allowed_timeframes:
            return normalized
        raise ValueError(f"Unsupported Bybit timeframe: {timeframe}")

    @staticmethod
    def _normalize_limit(limit: int) -> int:
        if limit < 1:
            raise ValueError("limit must be greater than zero")
        return min(limit, 200)

    @staticmethod
    def _normalize_order_book_limit(limit: int) -> int:
        if limit < 1:
            raise ValueError("limit must be greater than zero")
        return min(limit, 500)

    @staticmethod
    def _category(params: dict[str, Any] | None) -> str:
        category = (params or {}).get("category") or (params or {}).get("defaultType") or "spot"
        return str(category).lower()

    @classmethod
    def _ccxt_symbol(cls, symbol: str | None, params: dict[str, Any] | None = None) -> str:
        normalized = cls._normalize_symbol(symbol or "")
        category = cls._category(params)
        if category in {"linear", "swap", "future", "futures"}:
            base, quote = cls._split_symbol(normalized)
            return f"{base}/{quote}:{quote}"
        if category == "inverse":
            base, _quote = cls._split_symbol(normalized)
            return f"{base}:{base}"
        base, quote = cls._split_symbol(normalized)
        return f"{base}/{quote}"

    @staticmethod
    def _split_symbol(normalized_symbol: str) -> tuple[str, str]:
        quote_assets = ("USDT", "USDC", "FDUSD", "DAI", "TUSD", "USDP", "EUR", "USD", "BTC", "ETH")
        for quote in quote_assets:
            if normalized_symbol.endswith(quote) and len(normalized_symbol) > len(quote):
                return normalized_symbol[:-len(quote)], quote
        if len(normalized_symbol) >= 4:
            return normalized_symbol[:-4], normalized_symbol[-4:]
        raise ValueError("Invalid Bybit symbol")

    @staticmethod
    def _parse_candle(candle: list[float | int]) -> CandlePayload:
        if len(candle) < 6:
            raise ValueError("Invalid OHLCV payload")
        open_ms, open_value, high_value, low_value, close_value, volume_value = candle[:6]
        quote_volume = float(candle[6]) if len(candle) > 6 else None
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
            quote_volume=quote_volume,
        )


class BybitAdapter(BaseExchangeAdapter):
    exchange_id = "bybit"
    exchange_name = "Bybit"
    capabilities = ExchangeCapability(
        exchange_id="bybit",
        exchange_name="Bybit",
        asset_classes=("CRYPTO",),
        spot=True,
        futures=True,
        order_book=True,
        fetch_balances=True,
        fetch_positions=True,
        submit_order=True,
        cancel_order=True,
        fetch_order=True,
        supported_order_types=("MARKET", "LIMIT", "STOP_LIMIT", "STOP_MARKET", "TAKE_PROFIT", "TAKE_PROFIT_MARKET"),
        supported_time_in_force=("GTC", "IOC", "FOK"),
    )
    rate_limit_policy = {
        "fetch_candles": RateLimitPolicy(calls=120, period_seconds=60),
        "fetch_ticker": RateLimitPolicy(calls=120, period_seconds=60),
        "fetch_order_book": RateLimitPolicy(calls=120, period_seconds=60),
        "fetch_balances": RateLimitPolicy(calls=120, period_seconds=60),
        "fetch_positions": RateLimitPolicy(calls=120, period_seconds=60),
        "submit_order": RateLimitPolicy(calls=20, period_seconds=1),
        "cancel_order": RateLimitPolicy(calls=20, period_seconds=1),
        "fetch_order": RateLimitPolicy(calls=120, period_seconds=60),
    }

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
        testnet: bool = False,
        client: BybitClient | None = None,
    ) -> None:
        super().__init__(api_key=api_key, api_secret=api_secret, testnet=testnet)
        self.client = client or BybitClient(api_key=api_key, api_secret=api_secret, testnet=testnet)

    def normalize_symbol(self, symbol: str) -> str:
        return self.client._normalize_symbol(symbol)

    def fetch_candles(self, symbol: str, timeframe: str, limit: int, context: ExchangeOperationContext) -> list[UnifiedCandle]:
        if not self.rate_limit_manager.acquire("fetch_candles"):
            raise self.map_error(RuntimeError("Bybit candle rate limit exceeded"))
        params = self._context_params(context)
        try:
            raw_candles = self.client.fetch_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit, params=params)
        except Exception as exc:
            mapped = self.map_error(exc)
            self._mark_failure(mapped)
            raise mapped
        self._mark_success(self._now())
        return [self._to_unified_candle(candle, symbol, timeframe) for candle in raw_candles]

    def fetch_ticker(self, symbol: str, context: ExchangeOperationContext) -> UnifiedTicker:
        if not self.rate_limit_manager.acquire("fetch_ticker"):
            raise self.map_error(RuntimeError("Bybit ticker rate limit exceeded"))
        params = self._context_params(context)
        try:
            raw_ticker = self.client.fetch_ticker(symbol=symbol, params=params)
        except Exception as exc:
            mapped = self.map_error(exc)
            self._mark_failure(mapped)
            raise mapped
        self._mark_success(self._now())
        return self._to_unified_ticker(raw_ticker, symbol)

    def fetch_order_book(self, symbol: str, limit: int, context: ExchangeOperationContext) -> UnifiedOrderBook:
        if not self.rate_limit_manager.acquire("fetch_order_book"):
            raise self.map_error(RuntimeError("Bybit order book rate limit exceeded"))
        params = self._context_params(context)
        try:
            raw_order_book = self.client.fetch_order_book(symbol=symbol, limit=limit, params=params)
        except Exception as exc:
            mapped = self.map_error(exc)
            self._mark_failure(mapped)
            raise mapped
        self._mark_success(self._now())
        return self._to_unified_order_book(raw_order_book, symbol, limit)

    def fetch_balances(self, context: ExchangeOperationContext) -> list[UnifiedBalance]:
        if not self.rate_limit_manager.acquire("fetch_balances"):
            raise self.map_error(RuntimeError("Bybit balance rate limit exceeded"))
        params = self._context_params(context)
        try:
            raw_balance = self.client.fetch_balance(params=params)
        except Exception as exc:
            mapped = self.map_error(exc)
            self._mark_failure(mapped)
            raise mapped
        self._mark_success(self._now())
        return self._to_unified_balances(raw_balance, context)

    def fetch_positions(self, symbol: str, context: ExchangeOperationContext) -> list[UnifiedPosition]:
        if not self.rate_limit_manager.acquire("fetch_positions"):
            raise self.map_error(RuntimeError("Bybit position rate limit exceeded"))
        params = self._context_params(context, default_category="linear")
        try:
            raw_positions = self.client.fetch_positions(symbol=symbol, params=params)
        except Exception as exc:
            mapped = self.map_error(exc)
            self._mark_failure(mapped)
            raise mapped
        self._mark_success(self._now())
        return self._to_unified_positions(raw_positions, context)

    def submit_order(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: float,
        price: float | None,
        params: dict[str, Any] | None,
        context: ExchangeOperationContext,
    ) -> UnifiedOrder:
        if not self.rate_limit_manager.acquire("submit_order"):
            raise self.map_error(RuntimeError("Bybit submit order rate limit exceeded"))
        if not symbol:
            raise self.map_error(ValueError("symbol is required"))
        merged_params = self._context_params(context)
        merged_params.update(params or {})
        if context.idempotency_key:
            merged_params.setdefault("orderLinkId", context.idempotency_key)
        try:
            raw_order = self.client.create_order(
                symbol=symbol,
                side=side,
                type=type,
                quantity=quantity,
                price=price,
                params=merged_params,
            )
        except Exception as exc:
            mapped = self.map_error(exc)
            self._mark_failure(mapped)
            raise mapped
        self._mark_success(self._now())
        return self._to_unified_order(raw_order, context, side=side, order_type=type, price=price, quantity=quantity)

    def cancel_order(self, order_id: str, symbol: str, context: ExchangeOperationContext) -> UnifiedOrder:
        if not self.rate_limit_manager.acquire("cancel_order"):
            raise self.map_error(RuntimeError("Bybit cancel order rate limit exceeded"))
        params = self._context_params(context)
        try:
            raw_order = self.client.cancel_order(order_id=order_id, symbol=symbol, params=params)
        except Exception as exc:
            mapped = self.map_error(exc)
            self._mark_failure(mapped)
            raise mapped
        self._mark_success(self._now())
        return self._to_unified_order(raw_order, context)

    def fetch_order(self, order_id: str, symbol: str, context: ExchangeOperationContext) -> UnifiedOrder:
        if not self.rate_limit_manager.acquire("fetch_order"):
            raise self.map_error(RuntimeError("Bybit fetch order rate limit exceeded"))
        params = self._context_params(context)
        try:
            raw_order = self.client.fetch_order(order_id=order_id, symbol=symbol, params=params)
        except Exception as exc:
            mapped = self.map_error(exc)
            self._mark_failure(mapped)
            raise mapped
        self._mark_success(self._now())
        return self._to_unified_order(raw_order, context)

    def _to_unified_candle(self, candle: CandlePayload | list[float | int], symbol: str, timeframe: str) -> UnifiedCandle:
        normalized_symbol = self.normalize_symbol(symbol)
        base_asset, quote_asset = self._split_symbol(normalized_symbol)
        open_time = self._candle_open_time(candle)
        close_time = self._candle_close_time(candle, timeframe)
        quote_volume = self._candle_quote_volume(candle)
        trade_count = self._candle_trade_count(candle)
        return UnifiedCandle(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            source_symbol=symbol,
            normalized_symbol=normalized_symbol,
            base_asset=base_asset,
            quote_asset=quote_asset,
            timeframe=timeframe,
            open_time=open_time,
            close_time=close_time,
            open=self._candle_value(candle, 1),
            high=self._candle_value(candle, 2),
            low=self._candle_value(candle, 3),
            close=self._candle_value(candle, 4),
            volume=self._candle_value(candle, 5),
            quote_volume=quote_volume,
            trade_count=trade_count,
            source_timestamp=open_time,
            received_at=datetime.now(timezone.utc),
        )

    def _to_unified_ticker(self, raw_ticker: dict[str, Any], symbol: str) -> UnifiedTicker:
        normalized_symbol = self.normalize_symbol(symbol)
        return UnifiedTicker(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            source_symbol=symbol,
            normalized_symbol=normalized_symbol,
            last_price=self._first_float(raw_ticker.get("last"), raw_ticker.get("close"), raw_ticker.get("lastPrice")),
            bid_price=self._first_float(raw_ticker.get("bid"), raw_ticker.get("bidPrice")),
            ask_price=self._first_float(raw_ticker.get("ask"), raw_ticker.get("askPrice")),
            bid_size=self._first_float(raw_ticker.get("bidSize"), raw_ticker.get("bidsize"), raw_ticker.get("bid_quantity")),
            ask_size=self._first_float(raw_ticker.get("askSize"), raw_ticker.get("asksize"), raw_ticker.get("ask_quantity")),
            high_24h=self._first_float(raw_ticker.get("high"), raw_ticker.get("highPrice")),
            low_24h=self._first_float(raw_ticker.get("low"), raw_ticker.get("lowPrice")),
            volume_24h=self._first_float(raw_ticker.get("baseVolume"), raw_ticker.get("volume")),
            quote_volume_24h=self._first_float(raw_ticker.get("quoteVolume"), raw_ticker.get("quote_volume")),
            source_timestamp=self._datetime_from_value(raw_ticker.get("timestamp")),
            received_at=datetime.now(timezone.utc),
        )

    def _to_unified_order_book(self, raw_order_book: dict[str, Any], symbol: str, limit: int) -> UnifiedOrderBook:
        normalized_symbol = self.normalize_symbol(symbol)
        bids = tuple(
            OrderBookLevel(price=price, quantity=quantity)
            for level in raw_order_book.get("bids", [])
            if len(level) >= 2 and (price := self._first_float(level[0])) is not None and (quantity := self._first_float(level[1])) is not None
        )
        asks = tuple(
            OrderBookLevel(price=price, quantity=quantity)
            for level in raw_order_book.get("asks", [])
            if len(level) >= 2 and (price := self._first_float(level[0])) is not None and (quantity := self._first_float(level[1])) is not None
        )
        return UnifiedOrderBook(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            source_symbol=symbol,
            normalized_symbol=normalized_symbol,
            bids=bids,
            asks=asks,
            captured_at=datetime.now(timezone.utc),
            depth_level=limit,
        )

    def _to_unified_balances(self, raw_balance: dict[str, Any], context: ExchangeOperationContext) -> list[UnifiedBalance]:
        total = raw_balance.get("total") or {}
        free = raw_balance.get("free") or {}
        used = raw_balance.get("used") or {}
        currencies = {str(currency).upper() for currency in set(total) | set(free) | set(used)}
        currencies.discard("INFO")
        balances = []
        for currency in sorted(currencies):
            free_value = self._balance_value(free, currency)
            used_value = self._balance_value(used, currency)
            total_value = self._balance_value(total, currency)
            balances.append(
                UnifiedBalance(
                    exchange_id=self.exchange_id,
                    exchange_name=self.exchange_name,
                    user_id=context.user_id or "",
                    account_id=context.account_id or "",
                    currency=currency,
                    free=free_value,
                    used=used_value,
                    total=total_value,
                    available=free_value,
                    locked=used_value,
                    captured_at=datetime.now(timezone.utc),
                )
            )
        return balances

    def _to_unified_positions(self, raw_positions: Any, context: ExchangeOperationContext) -> list[UnifiedPosition]:
        raw_items = self._flatten_positions(raw_positions)
        positions = []
        for raw in raw_items:
            if not isinstance(raw, dict):
                continue
            symbol = raw.get("symbol") or ""
            normalized_symbol = self.normalize_symbol(symbol) if symbol else ""
            quantity = self._first_float(raw.get("contracts"), raw.get("size"), raw.get("amount")) or 0.0
            positions.append(
                UnifiedPosition(
                    exchange_id=self.exchange_id,
                    exchange_name=self.exchange_name,
                    user_id=context.user_id or "",
                    account_id=context.account_id or "",
                    source_symbol=symbol,
                    normalized_symbol=normalized_symbol,
                    quantity=quantity,
                    entry_price=self._first_float(raw.get("entryPrice"), raw.get("entry_price"), raw.get("avgEntryPrice")),
                    current_price=self._first_float(raw.get("markPrice"), raw.get("mark_price"), raw.get("lastPrice")),
                    mark_price=self._first_float(raw.get("markPrice"), raw.get("mark_price")),
                    side=self._normalize_side(raw.get("side")),
                    leverage=self._first_float(raw.get("leverage"), raw.get("leverageValue")),
                    margin_used=self._first_float(raw.get("initialMargin"), raw.get("initial_margin"), raw.get("margin"), raw.get("positionMargin")),
                    unrealized_pnl=self._first_float(raw.get("unrealizedPnl"), raw.get("unrealized_pnl")),
                    realized_pnl=self._first_float(raw.get("realizedPnl"), raw.get("realized_pnl")),
                    liquidation_price=self._first_float(raw.get("liquidationPrice"), raw.get("liquidation_price")),
                    captured_at=self._datetime_from_value(raw.get("timestamp")) or datetime.now(timezone.utc),
                )
            )
        return positions

    def _to_unified_order(self, raw_order: dict[str, Any], context: ExchangeOperationContext, **overrides: Any) -> UnifiedOrder:
        raw_order = raw_order or {}
        info = raw_order.get("info") if isinstance(raw_order.get("info"), dict) else {}
        symbol = raw_order.get("symbol") or overrides.get("symbol") or ""
        normalized_symbol = self.normalize_symbol(symbol) if symbol else None
        base_asset, quote_asset = self._split_symbol(normalized_symbol) if normalized_symbol else (None, None)
        quantity = overrides.get("quantity") if overrides.get("quantity") is not None else raw_order.get("amount")
        price = overrides.get("price") if overrides.get("price") is not None else raw_order.get("price")
        quantity_float = self._safe_float(quantity)
        filled_quantity = self._safe_float(raw_order.get("filled")) or 0.0
        remaining_quantity = self._safe_float(raw_order.get("remaining"))
        if remaining_quantity is None and quantity_float is not None:
            remaining_quantity = max(quantity_float - filled_quantity, 0.0)
        raw_status = raw_order.get("status") or raw_order.get("raw_status")
        status = self.map_order_status(str(raw_status)) if raw_status else overrides.get("status") or "NEW"
        client_order_id = self._first_present(raw_order.get("clientOrderId"), raw_order.get("orderLinkId"), info.get("orderLinkId"))
        return UnifiedOrder(
            internal_order_id=context.idempotency_key or client_order_id or str(raw_order.get("id") or ""),
            idempotency_key=context.idempotency_key or "",
            client_order_id=client_order_id,
            exchange_order_id=raw_order.get("id") or raw_order.get("exchange_order_id"),
            user_id=context.user_id,
            exchange_account_id=context.account_id,
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            source=context.metadata.get("source", "signal"),
            strategy_id=context.metadata.get("strategy_id"),
            signal_id=context.metadata.get("signal_id"),
            execution_source=context.metadata.get("execution_source"),
            routing_decision_id=context.metadata.get("routing_decision_id"),
            failover_attempt=int(context.metadata.get("failover_attempt", 0) or 0),
            primary_exchange_id=context.metadata.get("primary_exchange_id"),
            fallback_exchange_id=context.metadata.get("fallback_exchange_id"),
            source_symbol=symbol or None,
            normalized_symbol=normalized_symbol,
            base_asset=base_asset,
            quote_asset=quote_asset,
            asset_class="CRYPTO",
            side=self._normalize_side(overrides.get("side") or raw_order.get("side")),
            order_type=self._normalize_order_type(overrides.get("order_type") or raw_order.get("type"), raw_order, **overrides),
            time_in_force=self._normalize_time_in_force(raw_order.get("timeInForce") or raw_order.get("time_in_force")),
            quantity=quantity_float,
            quote_quantity=self._first_float(raw_order.get("cost"), raw_order.get("quote_quantity"), raw_order.get("quoteOrderQty")),
            price=self._safe_float(price),
            trigger_price=self._first_float(raw_order.get("triggerPrice"), raw_order.get("trigger_price"), info.get("triggerPrice")),
            stop_loss=self._first_float(raw_order.get("stopLoss"), raw_order.get("stop_loss"), info.get("stopLoss")),
            take_profit=self._first_float(raw_order.get("takeProfit"), raw_order.get("take_profit"), info.get("takeProfit")),
            status=status,
            raw_status=raw_status,
            filled_quantity=filled_quantity,
            remaining_quantity=remaining_quantity,
            average_price=self._first_float(raw_order.get("average"), raw_order.get("avgPrice")),
            last_fill_price=self._first_float(raw_order.get("lastTradePrice"), raw_order.get("lastFillPrice"), raw_order.get("last_price")),
            last_fill_time=self._datetime_from_value(raw_order.get("lastTradeTimestamp") or raw_order.get("last_fill_time")),
            fee_currency=self._fee_currency(raw_order),
            fee_amount=self._fee_amount(raw_order),
            commission=self._fee_amount(raw_order),
            notional_value=self._first_float(raw_order.get("cost"), raw_order.get("notional"), raw_order.get("notionalValue")),
            created_at=self._datetime_from_value(raw_order.get("timestamp")),
            submitted_at=self._datetime_from_value(raw_order.get("timestamp")),
            accepted_at=self._datetime_from_value(raw_order.get("timestamp")) if status != "REJECTED" else None,
            updated_at=self._datetime_from_value(raw_order.get("lastUpdateTimestamp") or raw_order.get("updated_at")),
            risk_decision_id=context.metadata.get("risk_decision_id"),
            pre_trade_check_id=context.metadata.get("pre_trade_check_id"),
            kill_switch_checked_at=self._datetime_from_value(context.metadata.get("kill_switch_checked_at")),
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
    def _candle_close_time(candle: CandlePayload | list[float | int], timeframe: str) -> datetime:
        if isinstance(candle, CandlePayload):
            return candle.close_time
        return datetime.fromtimestamp((int(candle[0]) + BybitAdapter._timeframe_to_ms(timeframe)) / 1000, tz=timezone.utc)

    @staticmethod
    def _candle_quote_volume(candle: CandlePayload | list[float | int]) -> float | None:
        if isinstance(candle, CandlePayload):
            return candle.quote_volume
        return BybitAdapter._safe_float(candle[6]) if len(candle) > 6 else None

    @staticmethod
    def _candle_trade_count(candle: CandlePayload | list[float | int]) -> int | None:
        value = BybitAdapter._safe_float(candle[7]) if isinstance(candle, list) and len(candle) > 7 else None
        return int(value) if value is not None else None

    @staticmethod
    def _timeframe_to_ms(timeframe: str) -> int:
        timeframe_ms = {
            "1m": 60_000,
            "3m": 180_000,
            "5m": 300_000,
            "15m": 900_000,
            "30m": 1_800_000,
            "1h": 3_600_000,
            "2h": 7_200_000,
            "4h": 14_400_000,
            "6h": 21_600_000,
            "12h": 43_200_000,
            "1d": 86_400_000,
            "1w": 604_800_000,
            "1M": 2_592_000_000,
        }
        return timeframe_ms.get(timeframe, 60_000)

    @staticmethod
    def _safe_float(value: object) -> float | None:
        if value is None:
            return None
        try:
            return float(str(value).replace(",", ""))
        except (TypeError, ValueError):
            return None

    @classmethod
    def _first_float(cls, *values: object) -> float | None:
        for value in values:
            converted = cls._safe_float(value)
            if converted is not None:
                return converted
        return None

    @staticmethod
    def _first_present(*values: object) -> str | None:
        for value in values:
            if value not in (None, ""):
                return str(value)
        return None

    @staticmethod
    def _datetime_from_value(value: object) -> datetime | None:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value / 1000, tz=timezone.utc)
        if isinstance(value, str) and value:
            try:
                parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        return None

    @staticmethod
    def _balance_value(balances: dict[str, Any], currency: str) -> float:
        if not balances:
            return 0.0
        value = balances.get(currency) or balances.get(currency.lower())
        return BybitAdapter._safe_float(value) or 0.0

    @staticmethod
    def _flatten_positions(raw_positions: Any) -> list[Any]:
        if isinstance(raw_positions, list):
            return raw_positions
        if isinstance(raw_positions, dict):
            flattened = []
            for value in raw_positions.values():
                if isinstance(value, list):
                    flattened.extend(value)
            return flattened
        return []

    @staticmethod
    def _split_symbol(normalized_symbol: str | None) -> tuple[str | None, str | None]:
        if not normalized_symbol:
            return None, None
        normalized = normalized_symbol.replace("/", "").replace("-", "").replace("_", "").replace(":", "")
        quote_assets = ("USDT", "USDC", "FDUSD", "DAI", "TUSD", "USDP", "EUR", "USD", "BTC", "ETH")
        for quote in quote_assets:
            if normalized.endswith(quote) and len(normalized) > len(quote):
                return normalized[:-len(quote)], quote
        if len(normalized) >= 4:
            return normalized[:-4], normalized[-4:]
        return normalized, None

    @staticmethod
    def _normalize_side(value: object) -> str | None:
        if value is None:
            return None
        return str(value).upper()

    @staticmethod
    def _normalize_order_type(value: object, raw_order: dict[str, Any], **overrides: Any) -> str | None:
        if value is None:
            return None
        normalized = str(value).upper().replace("-", "_").replace(" ", "_")
        mapping = {
            "LIMIT": "LIMIT",
            "MARKET": "MARKET",
            "STOP_LIMIT": "STOP_LIMIT",
            "STOP_MARKET": "STOP_MARKET",
            "TAKE_PROFIT": "TAKE_PROFIT",
            "TAKE_PROFIT_MARKET": "TAKE_PROFIT_MARKET",
            "STOPLOSS": "STOP_MARKET",
            "TAKEPROFIT": "TAKE_PROFIT_MARKET",
        }
        if normalized == "STOP":
            price = overrides.get("price") if overrides.get("price") is not None else raw_order.get("price")
            return "STOP_LIMIT" if price is not None else "STOP_MARKET"
        return mapping.get(normalized, normalized)

    @staticmethod
    def _normalize_time_in_force(value: object) -> str | None:
        if value is None:
            return None
        normalized = str(value).upper().replace("_", "").replace("-", "")
        mapping = {
            "GTC": "GTC",
            "GOODTILLCANCELLED": "GTC",
            "IOC": "IOC",
            "FOK": "FOK",
            "POSTONLY": "GTC",
        }
        return mapping.get(normalized, str(value).upper())

    @staticmethod
    def _fee_currency(raw_order: dict[str, Any]) -> str | None:
        fee = raw_order.get("fee")
        if isinstance(fee, dict):
            return fee.get("currency") or fee.get("code")
        return None

    @staticmethod
    def _fee_amount(raw_order: dict[str, Any]) -> float | None:
        fee = raw_order.get("fee")
        if isinstance(fee, dict):
            return BybitAdapter._safe_float(fee.get("cost") or fee.get("amount"))
        return None

    def _context_params(self, context: ExchangeOperationContext, default_category: str | None = None) -> dict[str, Any]:
        params = dict(context.metadata.get("params") or {})
        if default_category:
            params.setdefault("category", default_category)
        if context.metadata.get("category"):
            params["category"] = context.metadata["category"]
        return params

    @staticmethod
    def _now() -> float:
        return time.monotonic()

    def map_order_status(self, raw_status: str) -> str:
        status_map = {
            "NEW": "NEW",
            "OPEN": "NEW",
            "ACTIVE": "NEW",
            "UNTRIGGERED": "NEW",
            "TRIGGERED": "NEW",
            "PARTIALLY_FILLED": "PARTIALLY_FILLED",
            "PARTIALLYFILLED": "PARTIALLY_FILLED",
            "FILLED": "FILLED",
            "CLOSED": "FILLED",
            "CANCELED": "CANCELED",
            "CANCELLED": "CANCELED",
            "REJECTED": "REJECTED",
            "EXPIRED": "EXPIRED",
        }
        return status_map.get(raw_status.upper(), raw_status)
