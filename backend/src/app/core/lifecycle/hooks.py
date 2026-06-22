"""Lifecycle hook registration types."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from app.shared.enums import LifecyclePhase

LifecycleHookCallable = Callable[[object], Awaitable[None] | None]


@dataclass(frozen=True, slots=True)
class LifecycleHookRegistration:
    """Registered lifecycle hook."""

    name: str
    phase: LifecyclePhase
    callback: LifecycleHookCallable
    order: int = 0


@dataclass(frozen=True, slots=True)
class HookExecutionResult:
    """Result of executing a lifecycle hook."""

    name: str
    phase: LifecyclePhase
    duration_ms: float


__all__ = ["HookExecutionResult", "LifecycleHookCallable", "LifecycleHookRegistration"]
