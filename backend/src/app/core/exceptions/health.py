"""Health exception classes."""

from __future__ import annotations

from app.shared.enums import ErrorSeverity

from .base import CoreError


class HealthCheckError(CoreError):
    """A health check failed unexpectedly."""

    severity = ErrorSeverity.HIGH


__all__ = ["HealthCheckError"]
