from __future__ import annotations

import ccxt
from datetime import datetime, timezone
from typing import Any

from app.domain.exchange.models import (
    ExchangeCapability,
    ExchangeHealth,
    ExchangeOperationContext,
    UnifiedBalance,
    UnifiedCandle,
    UnifiedOrder,
    UnifiedOrderBook,
    UnifiedPosition,
    UnifiedTicker,
)
from app.integrations.exchanges.base import BaseExchangeAdapter
from app.integrations.exchanges.rate_limit import RateLimitPolicy


class OKXAdapter(BaseExchangeAdapter):
    exchange_id = "okx"
    exchange_name = "OKX"
    capabilities = ExchangeCapability(
        exchange_id="okx",
        exchange_name="OKX",
        asset_classes=("CRYPTO",),
        spot=True,
        futures=True,
        order_book=True,
        fetch_balances=True,
        fetch_positions=True,
        submit_order=True,
        supported_order_types=(
            "MARKET",
            "LIMIT",
            "STOP_LIMIT",
            "STOP_MARKET",
            "TAKE_PROFIT",
            "TAKE_PROFIT_MARKET",
            "MARGIN",
        ),
        supported_time_in_force=("GTC", "IOC", "FOK"),
    )
    rate_limit_policy = {
        "fetch_candles": RateLimitPolicy(calls=10, period_seconds=1),
        "fetch_ticker": RateLimitPolicy(calls=20, period_seconds=1),
        "fetch_order_book": RateLimitPolicy(calls=20, period_seconds=1),
        "fetch_balances": RateLimitPolicy(calls=10, period_seconds=1),
        "fetch_positions": RateLimitPolicy(calls=10, period_seconds=1),
        "submit_order": RateLimitPolicy(calls=10, period_seconds=1),
        "cancel_order": RateLimitPolicy(calls=10, period_seconds=1),
        "fetch_order": RateLimitPolicy(calls=10, period_seconds=1),
    }

    def __init__(self, api_key: str | None = None, api_secret: str | None = None, testnet: bool = False) -> None:
        super().__init__(api_key=api_key, api_secret=api_secret, testnet=testnet)
        self.exchange = self._create_exchange(api_key, api_secret, testnet)

    def _create_exchange(self, api_key: str | None, api_secret: str | None, testnet: bool) -> ccxt.okx:
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
            options["urls"] = {"api": "https://sandbox-api.okx.com"}
        return ccxt.okx(options)

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("/", "").replace("-", "").replace("_", "")

    def _ccxt_symbol(self, symbol: str) -> str:
        normalized = self.normalize_symbol(symbol)
        return normalized[:-4] + "/" + normalized[-4:] if len(normalized) >= 4 else normalized

    def fetch_candles(self, symbol: str, timeframe: str, limit: int, context: ExchangeOperationContext) -> list[UnifiedCandle]:
        if not self.rate_limit_manager.acquire("fetch_candles"):
            raise self.error_mapper.map_error(RuntimeError("OKX candle rate limit exceeded"))

        ccxt_symbol = self._ccxt_symbol(symbol)
        try:
            raw_candles = self.exchange.fetch_ohlcv(ccxt_symbol, timeframe=timeframe, limit=limit)
        except Exception as exc:
            self._mark_failure(self.map_error(exc))
            raise self.map_error(exc)

        self._mark_success(self._now())
        return [self._to_unified_candle(candle, symbol, timeframe) for candle in raw_candles]

    def fetch_ticker(self, symbol: str, context: ExchangeOperationContext) -> UnifiedTicker:
        if not self.rate_limit_manager.acquire("fetch_ticker"):
            raise self.error_mapper.map_error(RuntimeError("OKX ticker rate limit exceeded"))

        ccxt_symbol = self._ccxt_symbol(symbol)
        try:
            raw_ticker = self.exchange.fetch_ticker(ccxt_symbol)
        except Exception as exc:
            self._mark_failure(self.map_error(exc))
            raise self.map_error(exc)

        self._mark_success(self._now())
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

    def fetch_order_book(self, symbol: str, limit: int, context: ExchangeOperationContext) -> UnifiedOrderBook:
        if not self.rate_limit_manager.acquire("fetch_order_book"):
            raise self.error_mapper.map_error(RuntimeError("OKX order book rate limit exceeded"))

        ccxt_symbol = self._ccxt_symbol(symbol)
        try:
            raw_order_book = self.exchange.fetch_order_book(ccxt_symbol, limit=limit)
        except Exception as exc:
            self._mark_failure(self.map_error(exc))
            raise self.map_error(exc)

        self._mark_success(self._now())
        normalized_symbol = self.normalize_symbol(symbol)
        return UnifiedOrderBook(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            source_symbol=symbol,
            normalized_symbol=normalized_symbol,
            bids=tuple(UnifiedOrderBook.__dataclass_fields__["bids"].type(
                price=self._safe_float(bid[0]),
                quantity=self._safe_float(bid[1]),
            ) for bid in raw_order_book.get("bids", [])),
            asks=tuple(UnifiedOrderBook.__dataclass_fields__["asks"].type(
                price=self._safe_float(ask[0]),
                quantity=self._safe_float(ask[1]),
            ) for ask in raw_order_book.get("asks", [])),
            captured_at=datetime.now(timezone.utc),
        )

    def fetch_balances(self, context: ExchangeOperationContext) -> list[UnifiedBalance]:
        if not self.rate_limit_manager.acquire("fetch_balances"):
            raise self.error_mapper.map_error(RuntimeError("OKX balance rate limit exceeded"))

        try:
            raw_balance = self.exchange.fetch_balance()
        except Exception as exc:
            self._mark_failure(self.map_error(exc))
            raise self.map_error(exc)

        self._mark_success(self._now())
        return self._to_unified_balances(raw_balance, context)

    def fetch_positions(self, symbol: str, context: ExchangeOperationContext) -> list[UnifiedPosition]:
        if not self.rate_limit_manager.acquire("fetch_positions"):
            raise self.error_mapper.map_error(RuntimeError("OKX position rate limit exceeded"))

        ccxt_symbol = self._ccxt_symbol(symbol) if symbol else None
        try:
            raw_positions = self.exchange.fetch_positions([ccxt_symbol] if ccxt_symbol else None)
        except Exception as exc:
            self._mark_failure(self.map_error(exc))
            raise self.map_error(exc)

        self._mark_success(self._now())
        return self._to_unified_positions(raw_positions, context)

    def submit_order(self, payload: dict[str, Any], context: ExchangeOperationContext) -> UnifiedOrder:
        if not self.rate_limit_manager.acquire("submit_order"):
            raise self.error_mapper.map_error(RuntimeError("OKX submit order rate limit exceeded"))

        symbol = payload.get("symbol")
        side = payload.get("side")
        type_ = payload.get("type")
        quantity = payload.get("quantity")
        price = payload.get("price")
        params = payload.get("params", {})

        ccxt_symbol = self._ccxt_symbol(symbol) if symbol else None
        if not ccxt_symbol:
            raise self.error_mapper.map_error(ValueError("symbol is required"))

        try:
            raw_order = self.exchange.create_order(
                symbol=ccxt_symbol,
                type=type_,
                side=side,
                amount=quantity,
                price=price,
                params=params,
            )
        except Exception as exc:
            self._mark_failure(self.map_error(exc))
            raise self.map_error(exc)

        self._mark_success(self._now())
        return self._to_unified_order(raw_order, context, side=side, order_type=type_, price=price, quantity=quantity)

    def cancel_order(self, order_id: str, symbol: str, context: ExchangeOperationContext) -> UnifiedOrder:
        if not self.rate_limit_manager.acquire("cancel_order"):
            raise self.error_mapper.map_error(RuntimeError("OKX cancel order rate limit exceeded"))

        ccxt_symbol = self._ccxt_symbol(symbol)
        try:
            raw_order = self.exchange.cancel_order(order_id, ccxt_symbol)
        except Exception as exc:
            self._mark_failure(self.map_error(exc))
            raise self.map_error(exc)

        self._mark_success(self._now())
        return self._to_unified_order(raw_order, context)

    def fetch_order(self, order_id: str, symbol: str, context: ExchangeOperationContext) -> UnifiedOrder:
        if not self.rate_limit_manager.acquire("fetch_order"):
            raise self.error_mapper.map_error(RuntimeError("OKX fetch order rate limit exceeded"))

        ccxt_symbol = self._ccxt_symbol(symbol)
        try:
            raw_order = self.exchange.fetch_order(order_id, ccxt_symbol)
        except Exception as exc:
            self._mark_failure(self.map_error(exc))
            raise self.map_error(exc)

        self._mark_success(self._now())
        return self._to_unified_order(raw_order, context)

    def _to_unified_candle(self, candle: list[float | int], symbol: str, timeframe: str) -> UnifiedCandle:
        open_ms = int(candle[0])
        base_asset = self.normalize_symbol(symbol)[:-4]
        quote_asset = self.normalize_symbol(symbol)[-4:]
        return UnifiedCandle(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            source_symbol=symbol,
            normalized_symbol=self.normalize_symbol(symbol),
            base_asset=base_asset,
            quote_asset=quote_asset,
            timeframe=timeframe,
            open_time=datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc),
            close_time=datetime.fromtimestamp((open_ms + 60_000) / 1000, tz=timezone.utc),
            open=float(candle[1]),
            high=float(candle[2]),
            low=float(candle[3]),
            close=float(candle[4]),
            volume=float(candle[5]),
            source_timestamp=datetime.fromtimestamp(open_ms / 1000, tz=timezone.utc),
            received_at=datetime.now(timezone.utc),
        )

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

    def _to_unified_positions(self, raw_positions: list[dict[str, Any]], context: ExchangeOperationContext) -> list[UnifiedPosition]:
        positions = []
        for raw in raw_positions:
            symbol = raw.get("symbol", "")
            normalized_symbol = self.normalize_symbol(symbol)
            positions.append(
                UnifiedPosition(
                    exchange_id=self.exchange_id,
                    exchange_name=self.exchange_name,
                    user_id=context.user_id or "",
                    account_id=context.account_id or "",
                    source_symbol=symbol,
                    normalized_symbol=normalized_symbol,
                    quantity=float(raw.get("contracts", 0)),
                    entry_price=self._safe_float(raw.get("entryPrice")),
                    current_price=self._safe_float(raw.get("markPrice")),
                    mark_price=self._safe_float(raw.get("markPrice")),
                    side=raw.get("side"),
                    leverage=self._safe_float(raw.get("leverage")),
                    unrealized_pnl=self._safe_float(raw.get("unrealizedPnl")),
                    realized_pnl=self._safe_float(raw.get("realizedPnl")),
                    captured_at=datetime.now(timezone.utc),
                )
            )
        return positions

    def _to_unified_order(self, raw_order: dict[str, Any], context: ExchangeOperationContext, **overrides: Any) -> UnifiedOrder:
        symbol = raw_order.get("symbol", overrides.get("symbol", ""))
        return UnifiedOrder(
            internal_order_id=context.idempotency_key or "",
            idempotency_key=context.idempotency_key or "",
            client_order_id=raw_order.get("clientOrderId"),
            exchange_order_id=raw_order.get("id"),
            user_id=context.user_id or "",
            exchange_account_id=context.account_id or "",
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            source_symbol=symbol,
            normalized_symbol=self.normalize_symbol(symbol),
            base_asset=self.normalize_symbol(symbol)[:-4],
            quote_asset=self.normalize_symbol(symbol)[-4:],
            side=overrides.get("side") or raw_order.get("side"),
            order_type=overrides.get("order_type") or raw_order.get("type"),
            quantity=overrides.get("quantity") if overrides.get("quantity") is not None else raw_order.get("amount"),
            price=overrides.get("price") if overrides.get("price") is not None else raw_order.get("price"),
            status=self.map_order_status(raw_order.get("status", "")),
            raw_status=raw_order.get("status"),
            filled_quantity=float(raw_order.get("filled", 0)),
            remaining_quantity=float(raw_order.get("remaining", 0)),
            average_price=self._safe_float(raw_order.get("average")),
            created_at=self._datetime_from_value(raw_order.get("timestamp")),
            submitted_at=self._datetime_from_value(raw_order.get("timestamp")),
            updated_at=self._datetime_from_value(raw_order.get("lastUpdateTimestamp")),
        )

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

    @staticmethod
    def _now() -> float:
        import time
        return time.monotonic()
