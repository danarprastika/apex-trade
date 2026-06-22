"""Health report model."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from app.shared.enums import HealthStatus
from app.shared.types import JsonDict, JsonValue

from .checks import HealthCheckResult


@dataclass(frozen=True, slots=True)
class HealthReport:
    """Aggregated health report."""

    status: HealthStatus
    checked_at: datetime
    components: tuple[HealthCheckResult, ...]

    @classmethod
    def from_results(cls, results: list[HealthCheckResult]) -> HealthReport:
        """Create a report from check results."""
        return cls(
            status=_aggregate_status(results),
            checked_at=datetime.now(UTC),
            components=tuple(results),
        )

    def to_dict(self) -> JsonDict:
        """Convert the report to a JSON-serializable dictionary."""
        components: list[JsonValue] = [result.to_dict() for result in self.components]
        return {
            "status": self.status.value,
            "checked_at": self.checked_at.isoformat(),
            "components": components,
        }


def _aggregate_status(results: list[HealthCheckResult]) -> HealthStatus:
    """Aggregate component statuses."""
    if not results:
        return HealthStatus.UNKNOWN
    if any(result.status is HealthStatus.UNHEALTHY for result in results):
        return HealthStatus.UNHEALTHY
    if any(result.status is HealthStatus.DEGRADED for result in results):
        return HealthStatus.DEGRADED
    if any(result.status is HealthStatus.UNKNOWN for result in results):
        return HealthStatus.UNKNOWN
    return HealthStatus.HEALTHY


__all__ = ["HealthReport"]
