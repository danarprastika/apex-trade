"""Shared enumerations for the QuantX AI core package.

Enums provide strict, serializable values for environment selection, logging
levels, health status, lifecycle phases, and dependency lifetime scopes. All
values are string-based to remain stable across configuration files, logs, and
API responses.
"""

from __future__ import annotations

from enum import StrEnum


class Environment(StrEnum):
    """Supported runtime environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"

    @property
    def is_development(self) -> bool:
        """Return whether this environment is development."""
        return self is Environment.DEVELOPMENT

    @property
    def is_production(self) -> bool:
        """Return whether this environment is production."""
        return self is Environment.PRODUCTION

    @property
    def is_staging(self) -> bool:
        """Return whether this environment is staging."""
        return self is Environment.STAGING

    @property
    def is_testing(self) -> bool:
        """Return whether this environment is testing."""
        return self is Environment.TESTING


class LogLevel(StrEnum):
    """Supported logging levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

    def to_stdlib_level(self) -> int:
        """Return the equivalent Python logging level."""
        match self:
            case LogLevel.DEBUG:
                return 10
            case LogLevel.INFO:
                return 20
            case LogLevel.WARNING:
                return 30
            case LogLevel.ERROR:
                return 40
            case LogLevel.CRITICAL:
                return 50


class LogFormat(StrEnum):
    """Supported log output formats."""

    JSON = "json"
    TEXT = "text"


class HealthStatus(StrEnum):
    """Health status values used by health check reports."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"

    @property
    def is_available(self) -> bool:
        """Return whether the component is available for serving traffic."""
        return self in {HealthStatus.HEALTHY, HealthStatus.DEGRADED}


class HealthScope(StrEnum):
    """Health check scopes supported by the core package."""

    LIVE = "live"
    READY = "ready"
    DETAILED = "detailed"


class LifecyclePhase(StrEnum):
    """Ordered lifecycle phases for startup and shutdown."""

    BOOTSTRAP = "bootstrap"
    CONFIGURE_LOGGING = "configure_logging"
    VALIDATE_SETTINGS = "validate_settings"
    REGISTER_HEALTH_CHECKS = "register_health_checks"
    INITIALIZE_INFRASTRUCTURE = "initialize_infrastructure"
    START_BACKGROUND_TASKS = "start_background_tasks"
    RUNNING = "running"
    SHUTTING_DOWN = "shutting_down"
    SHUTDOWN = "shutdown"


STARTUP_PHASES: tuple[LifecyclePhase, ...] = (
    LifecyclePhase.BOOTSTRAP,
    LifecyclePhase.CONFIGURE_LOGGING,
    LifecyclePhase.VALIDATE_SETTINGS,
    LifecyclePhase.REGISTER_HEALTH_CHECKS,
    LifecyclePhase.INITIALIZE_INFRASTRUCTURE,
    LifecyclePhase.START_BACKGROUND_TASKS,
    LifecyclePhase.RUNNING,
)

SHUTDOWN_PHASES: tuple[LifecyclePhase, ...] = (
    LifecyclePhase.SHUTTING_DOWN,
    LifecyclePhase.SHUTDOWN,
)


class DependencyScope(StrEnum):
    """Dependency lifetime scopes supported by the registry."""

    TRANSIENT = "transient"
    SCOPED = "scoped"
    SINGLETON = "singleton"


__all__ = [
    "DependencyScope",
    "Environment",
    "HealthScope",
    "HealthStatus",
    "LifecyclePhase",
    "LogFormat",
    "LogLevel",
    "SHUTDOWN_PHASES",
    "STARTUP_PHASES",
]
