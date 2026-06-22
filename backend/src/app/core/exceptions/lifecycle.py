"""Lifecycle exception classes."""

from __future__ import annotations

from app.shared.enums import ErrorSeverity

from .base import CoreError


class LifecycleError(CoreError):
    """Lifecycle operation failed."""

    severity = ErrorSeverity.HIGH


class StartupError(LifecycleError):
    """Application startup failed."""

    severity = ErrorSeverity.CRITICAL


class ShutdownError(LifecycleError):
    """Application shutdown failed."""

    severity = ErrorSeverity.HIGH


__all__ = ["LifecycleError", "ShutdownError", "StartupError"]
