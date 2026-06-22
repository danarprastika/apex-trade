"""Lifecycle phase enumeration."""

from __future__ import annotations

from enum import StrEnum


class LifecyclePhase(StrEnum):
    """Ordered lifecycle phases for application startup and shutdown."""

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

__all__ = [
    "LifecyclePhase",
    "SHUTDOWN_PHASES",
    "STARTUP_PHASES",
]
