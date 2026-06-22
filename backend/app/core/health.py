"""Health check models and registry for the QuantX AI core package."""

from __future__ import annotations

import time
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Protocol, cast, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from .constants import DEFAULT_MAX_HEALTH_CHECKS
from .enums import HealthScope, HealthStatus
from .exceptions import HealthCheckError
from .metadata import ApplicationMetadata

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
type JsonDict = dict[str, JsonValue]


@runtime_checkable
class HealthCheck(Protocol):
    """Protocol implemented by health check components."""

    @property
    def name(self) -> str:
        """Return the health check name."""
        ...

    async def check(self) -> HealthCheckResult:
        """Run the health check and return its result."""
        ...


class HealthCheckResult(BaseModel):
    """Result of a single component health check."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    component: str = Field(min_length=1, max_length=128)
    status: HealthStatus
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    latency_ms: float = Field(ge=0)
    details: JsonDict = Field(default_factory=dict)
    error: str | None = None

    @property
    def healthy(self) -> bool:
        """Return whether the component is fully healthy."""
        return self.status is HealthStatus.HEALTHY

    @property
    def available(self) -> bool:
        """Return whether the component can serve traffic."""
        return self.status.is_available

    @classmethod
    def from_exception(
        cls,
        component: str,
        exc: BaseException,
        *,
        latency_ms: float = 0.0,
        details: Mapping[str, object] | None = None,
    ) -> HealthCheckResult:
        """Create an unhealthy result from an exception."""
        return cls(
            component=component,
            status=HealthStatus.UNHEALTHY,
            latency_ms=latency_ms,
            details=_json_dict(details or {}),
            error=str(exc),
        )


class HealthReport(BaseModel):
    """Aggregated health report for a scope."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    scope: HealthScope
    status: HealthStatus
    checked_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    results: dict[str, HealthCheckResult]
    metadata: ApplicationMetadata | None = None

    @property
    def healthy(self) -> bool:
        """Return whether every component is healthy."""
        return self.status is HealthStatus.HEALTHY

    @property
    def available(self) -> bool:
        """Return whether the application can serve traffic."""
        return self.status.is_available

    def to_dict(self) -> JsonDict:
        """Convert the report to a JSON-serializable dictionary."""
        return cast(JsonDict, self.model_dump(mode="json"))


class StaticHealthCheck:
    """Static health check returning a fixed result."""

    def __init__(
        self,
        name: str,
        status: HealthStatus = HealthStatus.HEALTHY,
        *,
        details: Mapping[str, object] | None = None,
        latency_ms: float = 0.0,
    ) -> None:
        """Create a static health check."""
        self._name = name
        self._status = status
        self._details = _json_dict(details or {})
        self._latency_ms = latency_ms

    @property
    def name(self) -> str:
        """Return the health check name."""
        return self._name

    async def check(self) -> HealthCheckResult:
        """Return the fixed health check result."""
        return HealthCheckResult(
            component=self._name,
            status=self._status,
            latency_ms=self._latency_ms,
            details=self._details,
        )


class HealthCheckRegistry:
    """Registry and executor for component health checks."""

    def __init__(
        self,
        checks: Mapping[str, HealthCheck] | None = None,
        *,
        max_checks: int = DEFAULT_MAX_HEALTH_CHECKS,
    ) -> None:
        """Create a health check registry."""
        if max_checks < 1:
            raise HealthCheckError(message="max_checks must be positive")
        self._max_checks = max_checks
        self._checks: dict[str, HealthCheck] = {}
        if checks is not None:
            for name, check in checks.items():
                self.register(name, check)

    def register(self, name: str, check: HealthCheck) -> HealthCheckRegistry:
        """Register a health check by name."""
        normalized_name = name.strip()
        if not normalized_name:
            raise HealthCheckError(message="Health check name must not be empty")
        if len(self._checks) >= self._max_checks:
            raise HealthCheckError(message="Maximum number of health checks reached")
        self._checks[normalized_name] = check
        return self

    def unregister(self, name: str) -> HealthCheckRegistry:
        """Unregister a health check by name."""
        self._checks.pop(name, None)
        return self

    def get(self, name: str) -> HealthCheck:
        """Return a registered health check."""
        try:
            return self._checks[name]
        except KeyError as exc:
            raise HealthCheckError(
                message=f"Health check '{name}' is not registered",
                details={"health_check": name},
            ) from exc

    def list_names(self) -> tuple[str, ...]:
        """Return registered health check names in sorted order."""
        return tuple(sorted(self._checks))

    async def check(self, name: str) -> HealthCheckResult:
        """Run a single health check and catch unexpected failures."""
        check = self.get(name)
        started_at = time.perf_counter()
        try:
            return await check.check()
        except Exception as exc:
            latency_ms = (time.perf_counter() - started_at) * 1000
            return HealthCheckResult.from_exception(name, exc, latency_ms=latency_ms)

    async def check_all(
        self,
        scope: HealthScope = HealthScope.DETAILED,
        metadata: ApplicationMetadata | None = None,
    ) -> HealthReport:
        """Run all registered health checks and aggregate the report."""
        results = {name: await self.check(name) for name in self.list_names()}
        status = HealthCheckRegistry.aggregate_status(results)
        return HealthReport(scope=scope, status=status, results=results, metadata=metadata)

    @staticmethod
    def aggregate_status(results: Mapping[str, HealthCheckResult]) -> HealthStatus:
        """Aggregate individual results into a report status."""
        if not results:
            return HealthStatus.UNKNOWN
        if all(result.healthy for result in results.values()):
            return HealthStatus.HEALTHY
        if all(not result.available for result in results.values()):
            return HealthStatus.UNHEALTHY
        return HealthStatus.DEGRADED


def _json_dict(value: Mapping[str, object]) -> JsonDict:
    """Convert mapping values into JSON-compatible values."""
    result: JsonDict = {}
    for key, item in value.items():
        result[str(key)] = _json_value(item)
    return result


def _json_value(value: object) -> JsonValue:
    """Convert a value into a JSON-compatible representation."""
    if value is None or isinstance(value, str | int | float | bool):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_value(item) for key, item in value.items()}
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, BaseException):
        return str(value)
    return str(value)


__all__ = [
    "HealthCheck",
    "HealthCheckRegistry",
    "HealthCheckResult",
    "HealthReport",
    "StaticHealthCheck",
]
