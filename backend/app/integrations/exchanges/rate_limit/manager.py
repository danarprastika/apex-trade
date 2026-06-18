from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RateLimitPolicy:
    calls: int
    period_seconds: float
    burst: int | None = None


class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float) -> None:
        self.capacity = capacity
        self.tokens = float(capacity)
        self.refill_rate = refill_rate
        self.updated_at = time.monotonic()

    def consume(self, tokens: int = 1) -> bool:
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    def wait_seconds(self, tokens: int = 1) -> float:
        self._refill()
        if self.tokens >= tokens:
            return 0.0
        missing = tokens - self.tokens
        return missing / self.refill_rate if self.refill_rate > 0 else self.capacity

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.updated_at
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.updated_at = now


class ExchangeRateLimitManager:
    def __init__(self, policies: dict[str, RateLimitPolicy] | None = None) -> None:
        self.policies = policies or {}
        self._buckets: dict[str, TokenBucket] = {}

    def get_policy(self, operation: str) -> RateLimitPolicy | None:
        return self.policies.get(operation)

    def acquire(self, operation: str, tokens: int = 1) -> bool:
        policy = self.get_policy(operation)
        if policy is None:
            return True

        bucket = self._get_bucket(operation, policy)
        return bucket.consume(tokens)

    def wait_seconds(self, operation: str, tokens: int = 1) -> float:
        policy = self.get_policy(operation)
        if policy is None:
            return 0.0

        bucket = self._get_bucket(operation, policy)
        return bucket.wait_seconds(tokens)

    def _get_bucket(self, operation: str, policy: RateLimitPolicy) -> TokenBucket:
        if operation not in self._buckets:
            burst = policy.burst or policy.calls
            refill_rate = policy.calls / policy.period_seconds
            self._buckets[operation] = TokenBucket(capacity=burst, refill_rate=refill_rate)
        return self._buckets[operation]
