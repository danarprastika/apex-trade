from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.exchange.models import ExchangeOperationContext
from app.domain.exchange.value_objects import ExchangeErrorCategory


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_seconds: float = 1.0
    max_delay_seconds: float = 30.0
    jitter: bool = True
    retryable_categories: frozenset[ExchangeErrorCategory] = frozenset(
        {
            ExchangeErrorCategory.RATE_LIMIT,
            ExchangeErrorCategory.NETWORK,
            ExchangeErrorCategory.TEMPORARY_EXCHANGE,
        }
    )


@dataclass(frozen=True)
class RetryDecision:
    should_retry: bool
    delay_seconds: float
    reason: str


class RetryManager:
    def __init__(self, policy: RetryPolicy | None = None) -> None:
        self.policy = policy or RetryPolicy()

    def should_retry(self, error: Exception, attempt: int) -> RetryDecision:
        category = getattr(error, "category", None)
        retry_after_seconds = getattr(error, "retry_after_seconds", None)
        retryable = getattr(error, "retryable", False)

        if attempt >= self.policy.max_attempts:
            return RetryDecision(False, 0.0, "retry budget exhausted")

        if retry_after_seconds is not None:
            return RetryDecision(True, float(retry_after_seconds), "retry-after provided by exchange")

        if retryable or category in self.policy.retryable_categories:
            return RetryDecision(True, self._delay_for_attempt(attempt), "retryable exchange error")

        return RetryDecision(False, 0.0, "non-retryable exchange error")

    def delay_for_attempt(self, attempt: int) -> float:
        return self._delay_for_attempt(max(1, attempt))

    def _delay_for_attempt(self, attempt: int) -> float:
        delay = self.policy.base_delay_seconds * (2 ** max(0, attempt - 1))
        return min(delay, self.policy.max_delay_seconds)

    async def execute(self, operation, context: ExchangeOperationContext) -> Any:
        attempt = 1
        while True:
            try:
                return await operation()
            except Exception as exc:
                decision = self.should_retry(exc, attempt)
                if not decision.should_retry:
                    raise
                attempt += 1
