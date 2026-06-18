from __future__ import annotations

from typing import Any

from app.integrations.exchanges.failover.policy import FailoverDecision, FailoverPolicy
from app.integrations.exchanges.registry import ExchangeAdapterRegistry


class ExchangeFailoverManager:
    def __init__(self, registry: ExchangeAdapterRegistry | None = None, policy: FailoverPolicy | None = None) -> None:
        self.registry = registry or ExchangeAdapterRegistry()
        self.policy = policy or FailoverPolicy()
        self._failed_operations: dict[str, int] = {}

    def evaluate_failover(self, operation: str, context: dict[str, Any]) -> FailoverDecision:
        if operation == "market_data":
            return self.policy.evaluate_market_data_failover(context)
        if operation == "order_execution":
            return self.policy.evaluate_order_execution_failover(context)
        return FailoverDecision(should_failover=False)

    def get_fallback_adapter(self, primary_exchange_key: str, operation: str) -> str | None:
        primary = self.registry.get(primary_exchange_key)
        if not primary:
            return None

        for key in self.registry.keys():
            if key == primary_exchange_key.lower():
                continue
            adapter = self.registry.get(key)
            if adapter and self._exchange_supports_operation(adapter, operation):
                return key
        return None

    def _exchange_supports_operation(self, adapter: Any, operation: str) -> bool:
        capabilities = adapter.get_capabilities()
        if operation in ("fetch_candles", "fetch_ticker", "fetch_order_book"):
            return capabilities.order_book or capabilities.spot
        if operation in ("fetch_balances", "fetch_positions"):
            return capabilities.fetch_balances or capabilities.fetch_positions
        if operation in ("submit_order", "cancel_order", "fetch_order"):
            return capabilities.submit_order or capabilities.cancel_order or capabilities.fetch_order
        return False

    def record_operation_result(self, exchange_key: str, success: bool) -> None:
        if success:
            self._failed_operations.pop(exchange_key, None)
        else:
            self._failed_operations[exchange_key] = self._failed_operations.get(exchange_key, 0) + 1

    def get_failure_count(self, exchange_key: str) -> int:
        return self._failed_operations.get(exchange_key, 0)