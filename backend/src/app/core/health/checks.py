"""Health check result model and static check implementation."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from app.shared.enums import HealthStatus
from app.shared.protocols import HealthCheck
from app.shared.types import JsonDict


@dataclass(frozen=True, slots=True)
class HealthCheckResult:
    """Result of a single health check."""

    name: str
    status: HealthStatus
    message: str
    details: JsonDict
    checked_at: datetime
    latency_ms: float

    @classmethod
    def healthy(
        cls, name: str, details: JsonDict | None = None, message: str = "OK"
    ) -> HealthCheckResult:
        """Create a healthy check result."""
        return cls._create(name, HealthStatus.HEALTHY, message, details or {})

    @classmethod
    def degraded(
        cls, name: str, details: JsonDict | None = None, message: str = "Degraded"
    ) -> HealthCheckResult:
        """Create a degraded check result."""
        return cls._create(name, HealthStatus.DEGRADED, message, details or {})

    @classmethod
    def unhealthy(
        cls, name: str, details: JsonDict | None = None, message: str = "Unhealthy"
    ) -> HealthCheckResult:
        """Create an unhealthy check result."""
        return cls._create(name, HealthStatus.UNHEALTHY, message, details or {})

    @classmethod
    def unknown(
        cls, name: str, details: JsonDict | None = None, message: str = "Unknown"
    ) -> HealthCheckResult:
        """Create an unknown check result."""
        return cls._create(name, HealthStatus.UNKNOWN, message, details or {})

    @staticmethod
    def _create(
        name: str,
        status: HealthStatus,
        message: str,
        details: JsonDict,
    ) -> HealthCheckResult:
        """Create a health check result with a timestamp."""
        return HealthCheckResult(
            name=name,
            status=status,
            message=message,
            details=details,
            checked_at=datetime.now(UTC),
            latency_ms=0.0,
        )

    def to_dict(self) -> JsonDict:
        """Convert the result to a JSON-serializable dictionary."""
        return {
            "name": self.name,
            "status": self.status.value,
            "message": self.message,
            "details": self.details,
            "checked_at": self.checked_at.isoformat(),
            "latency_ms": self.latency_ms,
        }


class StaticHealthCheck(HealthCheck):
    """Health check backed by a callable."""

    def __init__(self, name: str, checker: Callable[[], Any | Awaitable[Any]]) -> None:
        """Initialize the static health check."""
        self.name = name
        self._checker = checker

    async def check(self) -> Any:
        """Run the static checker."""
        return self._checker()


__all__ = ["HealthCheckResult", "StaticHealthCheck"]
