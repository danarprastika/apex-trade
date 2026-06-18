from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable


class CircuitState(Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5
    recovery_timeout_seconds: float = 60.0
    test_request_count: int = 1


class CircuitBreaker:
    def __init__(self, config: CircuitBreakerConfig | None = None) -> None:
        self.config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time: float | None = None
        self._test_requests_remaining = 0

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
                self._test_requests_remaining = self.config.test_request_count
        return self._state

    def _should_attempt_reset(self) -> bool:
        if self._last_failure_time is None:
            return False
        elapsed = time.monotonic() - self._last_failure_time
        return elapsed >= self.config.recovery_timeout_seconds

    def can_execute(self) -> bool:
        return self.state != CircuitState.OPEN or self._state == CircuitState.HALF_OPEN

    def record_success(self) -> None:
        self._failure_count = 0
        self._state = CircuitState.CLOSED
        self._test_requests_remaining = 0

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.config.failure_threshold:
            self._state = CircuitState.OPEN
            self._test_requests_remaining = 0

    def allow_request(self) -> bool:
        if self.state == CircuitState.HALF_OPEN:
            if self._test_requests_remaining > 0:
                self._test_requests_remaining -= 1
                return True
            return False
        return True

    async def execute(self, operation: Callable) -> any:
        if not self.allow_request():
            raise RuntimeError("Circuit breaker is OPEN - request blocked")

        try:
            result = await operation()
            self.record_success()
            return result
        except Exception:
            self.record_failure()
            raise