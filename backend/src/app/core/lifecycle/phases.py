"""Lifecycle phase constants."""

from __future__ import annotations

from app.shared.enums import LifecyclePhase

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

__all__ = ["LifecyclePhase", "SHUTDOWN_PHASES", "STARTUP_PHASES"]
