from __future__ import annotations

from typing import Any, Protocol

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
from app.integrations.exchanges.errors import ExchangeErrorMapper
from app.integrations.exchanges.rate_limit import ExchangeRateLimitManager
from app.integrations.exchanges.retry import RetryPolicy


class MarketDataAdapter(Protocol):
    def fetch_candles(self, symbol: str, timeframe: str, limit: int, context: ExchangeOperationContext) -> list[UnifiedCandle]: ...

    def fetch_ticker(self, symbol: str, context: ExchangeOperationContext) -> UnifiedTicker: ...

    def fetch_order_book(self, symbol: str, limit: int, context: ExchangeOperationContext) -> UnifiedOrderBook: ...


class OrderAdapter(Protocol):
    def submit_order(self, payload: dict[str, Any], context: ExchangeOperationContext) -> UnifiedOrder: ...

    def cancel_order(self, order_id: str, context: ExchangeOperationContext) -> UnifiedOrder: ...

    def fetch_order(self, order_id: str, context: ExchangeOperationContext) -> UnifiedOrder: ...


class PositionAdapter(Protocol):
    def fetch_balances(self, context: ExchangeOperationContext) -> list[UnifiedBalance]: ...

    def fetch_positions(self, context: ExchangeOperationContext) -> list[UnifiedPosition]: ...


class ExchangeAdapter(Protocol):
    exchange_id: str
    exchange_name: str
    capabilities: ExchangeCapability
    error_mapper: ExchangeErrorMapper
    rate_limit_manager: ExchangeRateLimitManager
    retry_policy: RetryPolicy

    def get_capabilities(self) -> ExchangeCapability: ...

    def get_health(self) -> ExchangeHealth: ...

    def normalize_symbol(self, symbol: str) -> str: ...

    def denormalize_symbol(self, normalized_symbol: str) -> str: ...

    def map_order_status(self, raw_status: str) -> str: ...

    def map_error(self, error: Exception) -> Exception: ...
