"""Health check aggregator."""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable
from datetime import UTC, datetime
from inspect import isawaitable
from time import perf_counter
from typing import cast

from app.shared.enums import HealthStatus
from app.shared.protocols import HealthCheck

from .checks import HealthCheckResult
from .report import HealthReport


class HealthAggregator:
    """Aggregate multiple health checks."""

    def __init__(self) -> None:
        """Initialize the aggregator."""
        self._checks: list[HealthCheck] = []

    def add(self, check: HealthCheck) -> None:
        """Register a health check."""
        self._checks.append(check)

    def remove(self, name: str) -> None:
        """Remove a health check by name."""
        self._checks = [check for check in self._checks if check.name != name]

    def names(self) -> tuple[str, ...]:
        """Return registered health check names."""
        return tuple(check.name for check in self._checks)

    async def check(self, name: str) -> HealthCheckResult:
        """Run a single health check by name."""
        check = next((item for item in self._checks if item.name == name), None)
        if check is None:
            return HealthCheckResult._create(
                name=name,
                status=HealthStatus.UNHEALTHY,
                message="Health check not found",
                details={"error": "Health check not found"},
            )

        return await self._run_check(check)

    async def check_all(self) -> HealthReport:
        """Run all registered health checks."""
        if not self._checks:
            return HealthReport.from_results([])
        tasks = [self._run_check(check) for check in self._checks]
        results = await asyncio.gather(*tasks)
        return HealthReport.from_results(results)

    async def _run_check(self, check: HealthCheck) -> HealthCheckResult:
        """Run a health check and convert exceptions to unhealthy results."""
        started = perf_counter()
        try:
            checked = cast(object | Awaitable[object], check.check())
            if isawaitable(checked):
                raw_result = await checked
            else:
                raw_result = checked
        except Exception as exc:  # noqa: BLE001
            latency_ms = (perf_counter() - started) * 1000
            return HealthCheckResult._create(
                name=check.name,
                status=HealthStatus.UNHEALTHY,
                message="Health check failed",
                details={"error": str(exc), "error_type": exc.__class__.__name__},
            )

        latency_ms = (perf_counter() - started) * 1000
        result = _coerce_result(check.name, raw_result, latency_ms)
        return result


def _coerce_result(name: str, raw_result: object, latency_ms: float) -> HealthCheckResult:
    """Coerce raw check output to a HealthCheckResult."""
    if isinstance(raw_result, HealthCheckResult):
        return HealthCheckResult(
            name=raw_result.name,
            status=raw_result.status,
            message=raw_result.message,
            details=raw_result.details,
            checked_at=raw_result.checked_at,
            latency_ms=latency_ms,
        )
    if isinstance(raw_result, dict):
        status_value = str(raw_result.get("status", HealthStatus.HEALTHY.value)).lower()
        status = _status_from_value(status_value)
        checked_at_value = raw_result.get("checked_at")
        checked_at = (
            checked_at_value if isinstance(checked_at_value, datetime) else datetime.now(UTC)
        )
        details_value = raw_result.get("details", {})
        details = details_value if isinstance(details_value, dict) else {}
        message_value = raw_result.get("message", status.value)
        return HealthCheckResult(
            name=name,
            status=status,
            message=str(message_value),
            details=dict(details),
            checked_at=checked_at,
            latency_ms=latency_ms,
        )
    return HealthCheckResult._create(
        name=name,
        status=HealthStatus.HEALTHY,
        message="OK",
        details={"value": str(raw_result)},
    )


def _status_from_value(value: str) -> HealthStatus:
    """Convert a string value to HealthStatus."""
    try:
        return HealthStatus(value)
    except ValueError:
        return HealthStatus.UNKNOWN


__all__ = ["HealthAggregator"]
