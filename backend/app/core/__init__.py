"""Core package for QuantX AI backend foundations.

This package contains framework-level primitives that are shared by the
application without depending on domain, infrastructure, or presentation
implementations. It provides validated settings, structured logging, lifecycle
management, health reporting, dependency registration, application metadata,
and typed core exceptions.
"""

from __future__ import annotations

from .config import CoreConfig, create_core_config, load_core_config, validate_core_settings
from .constants import (
    DEFAULT_APP_NAME,
    DEFAULT_APP_VERSION,
    DEFAULT_DETAILED_HEALTH_PATH,
    DEFAULT_ENVIRONMENT,
    DEFAULT_HEALTH_PATH,
    DEFAULT_HOST,
    DEFAULT_LIVENESS_PATH,
    DEFAULT_LOG_FORMAT,
    DEFAULT_LOG_LEVEL,
    DEFAULT_PORT,
    DEFAULT_READINESS_PATH,
    DEFAULT_WORKERS,
    ENV_FILE,
    ENV_PREFIX,
    PACKAGE_NAME,
    PYTHON_VERSION,
    SEMVER_PATTERN,
)
from .dependencies import DependencyProvider, DependencyRegistry
from .enums import (
    SHUTDOWN_PHASES,
    STARTUP_PHASES,
    DependencyScope,
    Environment,
    HealthScope,
    HealthStatus,
    LifecyclePhase,
    LogFormat,
    LogLevel,
)
from .exceptions import (
    CircularDependencyError,
    ConfigurationError,
    CoreError,
    DependencyAlreadyRegisteredError,
    DependencyInjectionError,
    DependencyNotFoundError,
    HealthCheckError,
    InvalidLifecycleTransitionError,
    LifecycleError,
    LoggingConfigurationError,
    SettingsValidationError,
)
from .health import (
    HealthCheck,
    HealthCheckRegistry,
    HealthCheckResult,
    HealthReport,
    StaticHealthCheck,
)
from .lifecycle import LifecycleHook, LifecycleManager
from .logging import (
    configure_logging,
    correlation_context,
    generate_correlation_id,
    get_correlation_id,
    get_logger,
    log_with_context,
    set_correlation_id,
)
from .metadata import ApplicationMetadata
from .settings import CoreSettings, load_settings

__all__ = [
    "CircularDependencyError",
    "ConfigurationError",
    "CoreConfig",
    "CoreError",
    "CoreSettings",
    "DependencyAlreadyRegisteredError",
    "DependencyInjectionError",
    "DependencyNotFoundError",
    "DependencyProvider",
    "DependencyRegistry",
    "DependencyScope",
    "Environment",
    "HealthCheck",
    "HealthCheckError",
    "HealthCheckRegistry",
    "HealthCheckResult",
    "HealthReport",
    "HealthScope",
    "HealthStatus",
    "InvalidLifecycleTransitionError",
    "LifecycleError",
    "LifecycleHook",
    "LifecycleManager",
    "LifecyclePhase",
    "LogFormat",
    "LogLevel",
    "LoggingConfigurationError",
    "SHUTDOWN_PHASES",
    "SettingsValidationError",
    "STARTUP_PHASES",
    "StaticHealthCheck",
    "ApplicationMetadata",
    "create_core_config",
    "configure_logging",
    "correlation_context",
    "generate_correlation_id",
    "get_correlation_id",
    "get_logger",
    "load_core_config",
    "load_settings",
    "log_with_context",
    "set_correlation_id",
    "validate_core_settings",
    "DEFAULT_APP_NAME",
    "DEFAULT_APP_VERSION",
    "DEFAULT_DETAILED_HEALTH_PATH",
    "DEFAULT_ENVIRONMENT",
    "DEFAULT_HEALTH_PATH",
    "DEFAULT_HOST",
    "DEFAULT_LIVENESS_PATH",
    "DEFAULT_LOG_FORMAT",
    "DEFAULT_LOG_LEVEL",
    "DEFAULT_PORT",
    "DEFAULT_READINESS_PATH",
    "DEFAULT_WORKERS",
    "ENV_FILE",
    "ENV_PREFIX",
    "PACKAGE_NAME",
    "PYTHON_VERSION",
    "SEMVER_PATTERN",
]
