"""Configuration exception classes."""

from __future__ import annotations

from app.shared.enums import ErrorSeverity

from .base import CoreError


class ConfigurationError(CoreError):
    """Configuration could not be loaded or applied."""

    severity = ErrorSeverity.CRITICAL


class SettingsValidationError(ConfigurationError):
    """Application settings failed validation."""

    severity = ErrorSeverity.CRITICAL


class SecretNotFoundError(ConfigurationError):
    """A required secret could not be resolved."""

    severity = ErrorSeverity.CRITICAL

    def __init__(self, name: str) -> None:
        """Initialize the missing secret error."""
        super().__init__(
            message=f"Required secret not found: {name}",
            code="SECRET_NOT_FOUND",
            details={"secret_name": name},
            user_message="Required secret is missing from the runtime environment.",
            severity=ErrorSeverity.CRITICAL,
        )


__all__ = ["ConfigurationError", "SecretNotFoundError", "SettingsValidationError"]
