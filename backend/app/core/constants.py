"""Constants for the QuantX AI core package.

The constants in this module define the stable defaults used by settings,
logging, health checks, lifecycle management, and metadata. Values are kept
immutable so the core package can be safely imported during application
bootstrap.
"""

from __future__ import annotations

import sys

from .enums import Environment, LogFormat, LogLevel

PACKAGE_NAME: str = "app.core"
DEFAULT_APP_NAME: str = "QuantX AI"
DEFAULT_APP_VERSION: str = "0.1.0"
PYTHON_VERSION: str = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
SEMVER_PATTERN: str = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:[-+][0-9A-Za-z.-]+)?$"

ENV_PREFIX: str = "QUANTX_"
ENV_FILE: str = ".env"

DEFAULT_ENVIRONMENT: Environment = Environment.DEVELOPMENT
DEFAULT_LOG_LEVEL: LogLevel = LogLevel.INFO
DEFAULT_LOG_FORMAT: LogFormat = LogFormat.JSON
DEFAULT_HOST: str = "0.0.0.0"
DEFAULT_PORT: int = 8000
DEFAULT_WORKERS: int = 1

DEFAULT_HEALTH_PATH: str = "/health"
DEFAULT_LIVENESS_PATH: str = "/health/live"
DEFAULT_READINESS_PATH: str = "/health/ready"
DEFAULT_DETAILED_HEALTH_PATH: str = "/health/detailed"

DEFAULT_CORRELATION_ID_HEADER: str = "X-Correlation-ID"
DEFAULT_STARTUP_TIMEOUT_SECONDS: float = 30.0
DEFAULT_SHUTDOWN_TIMEOUT_SECONDS: float = 30.0
DEFAULT_MAX_HEALTH_CHECKS: int = 100

DEFAULT_SENSITIVE_FIELD_NAMES: frozenset[str] = frozenset(
    {
        "api_key",
        "apikey",
        "authorization",
        "cookie",
        "credential",
        "password",
        "private_key",
        "secret",
        "set_cookie",
        "token",
    }
)

__all__ = [
    "DEFAULT_APP_NAME",
    "DEFAULT_APP_VERSION",
    "DEFAULT_CORRELATION_ID_HEADER",
    "DEFAULT_DETAILED_HEALTH_PATH",
    "DEFAULT_ENVIRONMENT",
    "DEFAULT_HEALTH_PATH",
    "DEFAULT_HOST",
    "DEFAULT_LOG_FORMAT",
    "DEFAULT_LOG_LEVEL",
    "DEFAULT_LIVENESS_PATH",
    "DEFAULT_MAX_HEALTH_CHECKS",
    "DEFAULT_PORT",
    "DEFAULT_READINESS_PATH",
    "DEFAULT_SENSITIVE_FIELD_NAMES",
    "DEFAULT_SHUTDOWN_TIMEOUT_SECONDS",
    "DEFAULT_STARTUP_TIMEOUT_SECONDS",
    "DEFAULT_WORKERS",
    "ENV_FILE",
    "ENV_PREFIX",
    "PACKAGE_NAME",
    "PYTHON_VERSION",
    "SEMVER_PATTERN",
]
