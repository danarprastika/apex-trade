"""Base exception classes for core technical failures."""

from __future__ import annotations

from app.shared.enums import ErrorSeverity
from app.shared.exceptions import QuantXBaseError


class CoreError(QuantXBaseError):
    """Base exception for QuantX AI core technical failures."""

    severity: ErrorSeverity = ErrorSeverity.MEDIUM


__all__ = ["CoreError"]
