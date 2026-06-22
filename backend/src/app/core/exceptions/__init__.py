"""Core exception package."""

from __future__ import annotations

from .base import CoreError
from .configuration import ConfigurationError, SecretNotFoundError, SettingsValidationError
from .dependency_injection import (
    DependencyInjectionError,
    ServiceRegistrationError,
    ServiceResolutionError,
)
from .health import HealthCheckError
from .lifecycle import LifecycleError, ShutdownError, StartupError
from .logging import LoggingConfigurationError

__all__ = [
    "ConfigurationError",
    "CoreError",
    "DependencyInjectionError",
    "HealthCheckError",
    "LifecycleError",
    "LoggingConfigurationError",
    "SecretNotFoundError",
    "ServiceRegistrationError",
    "ServiceResolutionError",
    "SettingsValidationError",
    "ShutdownError",
    "StartupError",
]
