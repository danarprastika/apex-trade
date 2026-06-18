from __future__ import annotations

from app.integrations.exchanges.base.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
)
from app.integrations.exchanges.failover.manager import ExchangeFailoverManager
from app.integrations.exchanges.failover.policy import FailoverPolicy
from app.integrations.exchanges.registry import ExchangeAdapterRegistry


class TestCircuitBreaker:
    def test_initial_state_is_closed(self) -> None:
        breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=3))
        assert breaker.state == CircuitState.CLOSED

    def test_success_resets_failure_count(self) -> None:
        breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=3))
        breaker.record_failure()
        breaker.record_failure()
        breaker.record_success()
        assert breaker.state == CircuitState.CLOSED
        assert breaker._failure_count == 0

    def test_transitions_to_open_after_threshold(self) -> None:
        breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=3, recovery_timeout_seconds=60))
        for _ in range(3):
            breaker.record_failure()
        assert breaker.state == CircuitState.OPEN

    def test_can_execute_returns_false_when_open(self) -> None:
        breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=2))
        breaker.record_failure()
        breaker.record_failure()
        assert breaker.can_execute() is False

    def test_allow_request_allows_in_half_open(self) -> None:
        breaker = CircuitBreaker(CircuitBreakerConfig(failure_threshold=2, recovery_timeout_seconds=0.01))
        breaker.record_failure()
        breaker.record_failure()
        import time
        time.sleep(0.02)
        assert breaker.allow_request() is True


class TestFailoverPolicy:
    def test_evaluate_market_data_failover_on_unavailable(self) -> None:
        policy = FailoverPolicy()
        context = {"exchange_health": {"available": False}}
        decision = policy.evaluate_market_data_failover(context)
        assert decision.should_failover is True
        assert "unavailable" in (decision.failover_reason or "").lower()

    def test_evaluate_market_data_failover_on_high_latency(self) -> None:
        policy = FailoverPolicy(latency_threshold_ms=100.0)
        context = {"exchange_health": {"available": True, "latency_ms": 500.0}}
        decision = policy.evaluate_market_data_failover(context)
        assert decision.should_failover is True

    def test_evaluate_market_data_failover_on_healthy_exchange(self) -> None:
        policy = FailoverPolicy()
        context = {"exchange_health": {"available": True, "latency_ms": 50.0, "error_rate": 0.01}}
        decision = policy.evaluate_market_data_failover(context)
        assert decision.should_failover is False


class TestExchangeFailoverManager:
    def test_evaluate_failover_uses_policy(self) -> None:
        registry = ExchangeAdapterRegistry()
        manager = ExchangeFailoverManager(registry=registry)
        context = {"exchange_health": {"available": False}}
        decision = manager.evaluate_failover("market_data", context)
        assert decision.should_failover is True

    def test_record_operation_result_tracks_failures(self) -> None:
        registry = ExchangeAdapterRegistry()
        manager = ExchangeFailoverManager(registry=registry)
        manager.record_operation_result("binance", success=False)
        manager.record_operation_result("binance", success=False)
        assert manager.get_failure_count("binance") == 2

    def test_success_resets_failure_count(self) -> None:
        registry = ExchangeAdapterRegistry()
        manager = ExchangeFailoverManager(registry=registry)
        manager.record_operation_result("binance", success=False)
        manager.record_operation_result("binance", success=True)
        assert manager.get_failure_count("binance") == 0
