"""Dependency injection exception classes."""

from __future__ import annotations

from app.shared.enums import ErrorSeverity

from .base import CoreError


class DependencyInjectionError(CoreError):
    """Dependency injection failed."""

    severity = ErrorSeverity.HIGH


class ServiceRegistrationError(DependencyInjectionError):
    """A service could not be registered."""

    severity = ErrorSeverity.HIGH


class ServiceResolutionError(DependencyInjectionError):
    """A service could not be resolved."""

    severity = ErrorSeverity.HIGH


__all__ = ["DependencyInjectionError", "ServiceRegistrationError", "ServiceResolutionError"]
