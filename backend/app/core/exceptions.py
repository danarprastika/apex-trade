"""Typed exception hierarchy for the QuantX AI core package.

Core exceptions carry stable machine-readable metadata for structured logging,
health reporting, and dependency management. They avoid leaking infrastructure
details while preserving the original exception chain for operators.
"""

from __future__ import annotations

from collections.abc import Mapping

from .enums import LogLevel

type JsonPrimitive = str | int | float | bool | None
type JsonValue = JsonPrimitive | list["JsonValue"] | dict[str, "JsonValue"]
type JsonDict = dict[str, JsonValue]


class CoreError(Exception):
    """Base class for QuantX AI core failures."""

    code: str = "CORE_ERROR"
    retryable: bool = False
    severity: LogLevel = LogLevel.ERROR

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        details: Mapping[str, object] | None = None,
        retryable: bool | None = None,
        severity: LogLevel | None = None,
        user_message: str | None = None,
    ) -> None:
        """Create a typed core exception."""
        if not message.strip():
            raise ValueError("message must not be empty")
        if code is not None and not code.strip():
            raise ValueError("code must not be empty")

        self.message = message
        self.code = code or self.__class__.code
        self.details = dict(details) if details is not None else None
        self.retryable = self.__class__.retryable if retryable is None else retryable
        self.severity = severity or self.__class__.severity
        self.user_message = user_message
        super().__init__(message)

    def to_dict(self) -> JsonDict:
        """Convert the exception to a JSON-serializable dictionary."""
        data: JsonDict = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "severity": self.severity.value,
        }
        if self.details is not None:
            data["details"] = self._json_dict(self.details)
        if self.user_message is not None:
            data["user_message"] = self.user_message
        return data

    @property
    def context(self) -> dict[str, object]:
        """Return logging-friendly context for structured log records."""
        context: dict[str, object] = {
            "error_code": self.code,
            "error_message": self.message,
            "error_severity": self.severity.value,
            "error_retryable": self.retryable,
        }
        if self.details:
            context["error_details"] = self._json_dict(self.details)
        if self.user_message is not None:
            context["user_message"] = self.user_message
        return context

    def _json_dict(self, value: Mapping[str, object]) -> JsonDict:
        """Convert arbitrary mapping values into JSON-compatible values."""
        result: JsonDict = {}
        for key, item in value.items():
            result[str(key)] = self._json_value(item)
        return result

    def _json_value(self, value: object) -> JsonValue:
        """Convert a value into a JSON-compatible representation."""
        if value is None or isinstance(value, str | int | float | bool):
            return value
        if isinstance(value, Mapping):
            return {str(key): self._json_value(item) for key, item in value.items()}
        return str(value)


class ConfigurationError(CoreError):
    """Configuration could not be loaded or validated."""

    code = "CONFIGURATION_ERROR"
    retryable = False
    severity = LogLevel.CRITICAL


class SettingsValidationError(ConfigurationError):
    """Core settings failed validation."""

    code = "SETTINGS_VALIDATION_ERROR"


class LoggingConfigurationError(ConfigurationError):
    """Structured logging could not be configured."""

    code = "LOGGING_CONFIGURATION_ERROR"


class LifecycleError(CoreError):
    """Application lifecycle operation failed."""

    code = "LIFECYCLE_ERROR"
    retryable = False
    severity = LogLevel.ERROR


class InvalidLifecycleTransitionError(LifecycleError):
    """Lifecycle transition is not allowed from the current phase."""

    code = "INVALID_LIFECYCLE_TRANSITION"


class HealthCheckError(CoreError):
    """Health check operation failed."""

    code = "HEALTH_CHECK_ERROR"
    retryable = True
    severity = LogLevel.ERROR


class DependencyInjectionError(CoreError):
    """Dependency registry operation failed."""

    code = "DEPENDENCY_INJECTION_ERROR"
    retryable = False
    severity = LogLevel.ERROR


class DependencyNotFoundError(DependencyInjectionError):
    """Requested dependency is not registered."""

    code = "DEPENDENCY_NOT_FOUND"

    def __init__(self, dependency_name: str) -> None:
        """Create a dependency-not-found error."""
        super().__init__(
            message=f"Dependency '{dependency_name}' is not registered",
            details={"dependency": dependency_name},
            user_message="A required application dependency is missing",
        )


class DependencyAlreadyRegisteredError(DependencyInjectionError):
    """Dependency is already registered for the same interface."""

    code = "DEPENDENCY_ALREADY_REGISTERED"

    def __init__(self, dependency_name: str) -> None:
        """Create a duplicate-dependency error."""
        super().__init__(
            message=f"Dependency '{dependency_name}' is already registered",
            details={"dependency": dependency_name},
            user_message="A required application dependency is duplicated",
        )


class CircularDependencyError(DependencyInjectionError):
    """Dependency resolution detected a cycle."""

    code = "CIRCULAR_DEPENDENCY"

    def __init__(self, dependency_name: str) -> None:
        """Create a circular-dependency error."""
        super().__init__(
            message=f"Circular dependency detected while resolving '{dependency_name}'",
            details={"dependency": dependency_name},
            user_message="Application dependencies contain a cycle",
        )


__all__ = [
    "CircularDependencyError",
    "ConfigurationError",
    "CoreError",
    "DependencyAlreadyRegisteredError",
    "DependencyInjectionError",
    "DependencyNotFoundError",
    "HealthCheckError",
    "InvalidLifecycleTransitionError",
    "LifecycleError",
    "LoggingConfigurationError",
    "SettingsValidationError",
]
