from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.domain.exchange.models import (
    ExchangeCapability,
    ExchangeHealth,
    ExchangeOperationContext,
    UnifiedBalance,
    UnifiedCandle,
    UnifiedOrderBook,
    UnifiedPosition,
    UnifiedTicker,
)
from app.domain.exchange.value_objects import ExchangeErrorCategory
from app.integrations.exchanges.errors import ExchangeErrorMapper, ExchangeIntegrationError
from app.integrations.exchanges.interfaces import ExchangeAdapter, MarketDataAdapter, OrderAdapter, PositionAdapter
from app.integrations.exchanges.rate_limit import ExchangeRateLimitManager, RateLimitPolicy
from app.integrations.exchanges.retry import RetryPolicy
from app.integrations.exchanges.base.circuit_breaker import CircuitBreaker, CircuitBreakerConfig


class BaseExchangeAdapter:
    exchange_id = "base"
    exchange_name = "BaseExchange"
    capabilities = ExchangeCapability(exchange_id="base", exchange_name="BaseExchange")
    retry_policy = RetryPolicy()
    rate_limit_policy: dict[str, RateLimitPolicy] = {}

    def __init__(
        self,
        *,
        api_key: str | None = None,
        api_secret: str | None = None,
        testnet: bool = False,
        capabilities: ExchangeCapability | None = None,
        retry_policy: RetryPolicy | None = None,
        rate_limit_policy: dict[str, RateLimitPolicy] | None = None,
        circuit_breaker_config: CircuitBreakerConfig | None = None,
    ) -> None:
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.capabilities = capabilities or self.capabilities
        self.retry_policy = retry_policy or self.retry_policy
        self.error_mapper = ExchangeErrorMapper()
        self.rate_limit_manager = ExchangeRateLimitManager(rate_limit_policy or self.rate_limit_policy)
        self.circuit_breaker = CircuitBreaker(circuit_breaker_config)
        self.last_health = ExchangeHealth(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            available=False,
            last_checked_at=None,
        )

    def get_capabilities(self) -> ExchangeCapability:
        return self.capabilities

    def get_health(self) -> ExchangeHealth:
        return self.last_health

    def normalize_symbol(self, symbol: str) -> str:
        return symbol.upper().replace("/", "").replace("-", "").replace("_", "")

    def denormalize_symbol(self, normalized_symbol: str) -> str:
        return normalized_symbol.upper()

    def map_order_status(self, raw_status: str) -> str:
        normalized = raw_status.upper()
        status_map = {
            "NEW": "NEW",
            "PARTIALLY_FILLED": "PARTIALLY_FILLED",
            "FILLED": "FILLED",
            "CANCELED": "CANCELED",
            "CANCELLED": "CANCELED",
            "REJECTED": "REJECTED",
            "EXPIRED": "EXPIRED",
        }
        return status_map.get(normalized, normalized)

    def map_error(self, error: Exception) -> Exception:
        return self.error_mapper.map_error(error, exchange_name=self.exchange_name)

    def _context(self, operation: str, symbol: str | None = None, **metadata: Any) -> ExchangeOperationContext:
        return ExchangeOperationContext(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            operation=operation,
            symbol=symbol,
            metadata=metadata,
        )

    def _mark_success(self, started_at: float) -> None:
        self.last_health = ExchangeHealth(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            available=True,
            latency_ms=None,
            last_checked_at=datetime.now(timezone.utc),
        )

    def _mark_failure(self, error: Exception) -> None:
        self.last_health = ExchangeHealth(
            exchange_id=self.exchange_id,
            exchange_name=self.exchange_name,
            available=False,
            last_checked_at=datetime.now(timezone.utc),
            last_error=str(error),
        )

    def get_capabilities_model(self) -> ExchangeCapability:
        return self.capabilities

    def fetch_candles(self, symbol: str, timeframe: str, limit: int, context: ExchangeOperationContext) -> list[UnifiedCandle]:
        raise NotImplementedError

    def fetch_ticker(self, symbol: str, context: ExchangeOperationContext) -> UnifiedTicker:
        raise NotImplementedError

    def fetch_order_book(self, symbol: str, limit: int, context: ExchangeOperationContext) -> UnifiedOrderBook:
        raise NotImplementedError

    def submit_order(self, payload: dict[str, Any], context: ExchangeOperationContext) -> UnifiedOrder:
        raise NotImplementedError

    def cancel_order(self, order_id: str, context: ExchangeOperationContext) -> UnifiedOrder:
        raise NotImplementedError

    def fetch_order(self, order_id: str, context: ExchangeOperationContext) -> UnifiedOrder:
        raise NotImplementedError

    def fetch_balances(self, context: ExchangeOperationContext) -> list[UnifiedBalance]:
        raise NotImplementedError

    def fetch_positions(self, context: ExchangeOperationContext) -> list[UnifiedPosition]:
        raise NotImplementedError
