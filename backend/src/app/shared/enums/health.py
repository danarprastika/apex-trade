"""Health status and scope enumerations."""

from __future__ import annotations

from enum import StrEnum


class HealthStatus(StrEnum):
    """Health status values returned by health checks."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthScope(StrEnum):
    """Health check scope values."""

    LIVE = "live"
    READY = "ready"
    DETAILED = "detailed"


__all__ = ["HealthScope", "HealthStatus"]
