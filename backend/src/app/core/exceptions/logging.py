"""Logging exception classes."""

from __future__ import annotations

from app.shared.enums import ErrorSeverity

from .base import CoreError


class LoggingConfigurationError(CoreError):
    """Logging could not be configured."""

    severity = ErrorSeverity.CRITICAL


__all__ = ["LoggingConfigurationError"]
