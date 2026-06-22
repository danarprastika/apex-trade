"""Lifecycle manager implementation."""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from inspect import isawaitable

from app.core.exceptions import LifecycleError
from app.core.metadata import AppMetadata
from app.shared.enums import LifecyclePhase

from .hooks import HookExecutionResult, LifecycleHookCallable, LifecycleHookRegistration
from .phases import SHUTDOWN_PHASES, STARTUP_PHASES


@dataclass(frozen=True, slots=True)
class LifecycleContext:
    """Context passed to lifecycle hooks."""

    metadata: AppMetadata
    phase: LifecyclePhase


class LifecycleManager:
    """Manage startup and shutdown lifecycle hooks."""

    def __init__(self, metadata: AppMetadata) -> None:
        """Initialize the lifecycle manager."""
        self._metadata = metadata
        self._hooks: dict[LifecyclePhase, list[LifecycleHookRegistration]] = defaultdict(list)
        self._started = False

    @property
    def metadata(self) -> AppMetadata:
        """Return application metadata."""
        return self._metadata

    @property
    def started(self) -> bool:
        """Return whether startup has completed."""
        return self._started

    def register_hook(
        self,
        *,
        name: str,
        phase: LifecyclePhase,
        callback: LifecycleHookCallable,
        order: int = 0,
    ) -> None:
        """Register a lifecycle hook."""
        if not name.strip():
            raise LifecycleError("Hook name must not be empty", "EMPTY_HOOK_NAME")
        registration = LifecycleHookRegistration(
            name=name, phase=phase, callback=callback, order=order
        )
        self._hooks[phase].append(registration)
        self._hooks[phase].sort(key=lambda hook: (hook.order, hook.name))

    async def run_phase(self, phase: LifecyclePhase) -> list[HookExecutionResult]:
        """Run all hooks for a lifecycle phase."""
        context = LifecycleContext(metadata=self._metadata, phase=phase)
        results: list[HookExecutionResult] = []
        for registration in self._hooks.get(phase, []):
            started = time.perf_counter()
            result = registration.callback(context)
            if isawaitable(result):
                await result
            duration_ms = (time.perf_counter() - started) * 1000
            results.append(
                HookExecutionResult(name=registration.name, phase=phase, duration_ms=duration_ms)
            )
        return results

    async def start(self) -> list[HookExecutionResult]:
        """Run startup phases in order."""
        if self._started:
            return []
        results: list[HookExecutionResult] = []
        for phase in STARTUP_PHASES:
            results.extend(await self.run_phase(phase))
        self._started = True
        return results

    async def shutdown(self) -> list[HookExecutionResult]:
        """Run shutdown phases in order."""
        results: list[HookExecutionResult] = []
        for phase in SHUTDOWN_PHASES:
            results.extend(await self.run_phase(phase))
        self._started = False
        return results


__all__ = ["LifecycleContext", "LifecycleManager"]
