from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class FailoverDecision:
    should_failover: bool
    failover_reason: str | None = None
    fallback_exchange_id: str | None = None
    requires_manual_approval: bool = False


@dataclass
class FailoverPolicy:
    allow_market_data_failover: bool = True
    allow_account_sync_failover: bool = False
    allow_order_execution_failover: bool = False
    max_failover_attempts: int = 3
    health_threshold_percentage: float = 0.7
    latency_threshold_ms: float = 500.0

    def evaluate_market_data_failover(self, context: dict[str, Any]) -> FailoverDecision:
        exchange_health = context.get("exchange_health")
        if not exchange_health:
            return FailoverDecision(should_failover=False)

        available = exchange_health.get("available", True)
        if not available:
            return FailoverDecision(
                should_failover=True,
                failover_reason="Exchange unavailable",
                requires_manual_approval=False,
            )

        latency = exchange_health.get("latency_ms", 0)
        if latency and latency > self.latency_threshold_ms:
            return FailoverDecision(
                should_failover=True,
                failover_reason="Exchange latency exceeded threshold",
                requires_manual_approval=False,
            )

        error_rate = exchange_health.get("error_rate", 0)
        if error_rate and error_rate > self.health_threshold_percentage:
            return FailoverDecision(
                should_failover=True,
                failover_reason="Exchange error rate exceeded threshold",
                requires_manual_approval=False,
            )

        return FailoverDecision(should_failover=False)

    def evaluate_order_execution_failover(self, context: dict[str, Any]) -> FailoverDecision:
        if not self.allow_order_execution_failover:
            return FailoverDecision(should_failover=False)

        order_submitted = context.get("order_already_submitted", False)
        if order_submitted:
            return FailoverDecision(
                should_failover=False,
                failover_reason="Order already submitted - failover not safe",
            )

        strategy_supports_multi_exchange = context.get("strategy_supports_multi_exchange", False)
        if not strategy_supports_multi_exchange:
            return FailoverDecision(
                should_failover=False,
                failover_reason="Strategy does not support multi-exchange routing",
            )

        return FailoverDecision(should_failover=True, requires_manual_approval=True)