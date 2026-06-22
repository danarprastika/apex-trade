"""Application lifecycle management for the QuantX AI core package.

The lifecycle manager coordinates ordered startup and shutdown hooks while
preserving the current lifecycle phase. It is intentionally framework-neutral so
FastAPI, workers, and tests can use the same lifecycle semantics.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable, Sequence
from datetime import UTC, datetime
from typing import cast

from .enums import SHUTDOWN_PHASES, STARTUP_PHASES, LifecyclePhase
from .exceptions import InvalidLifecycleTransitionError

LifecycleHook = Callable[[], Awaitable[None] | None]


class LifecycleManager:
    """Manage ordered application startup and shutdown phases."""

    def __init__(self) -> None:
        """Create an empty lifecycle manager."""
        self._phase = LifecyclePhase.BOOTSTRAP
        self._startup_hooks: dict[LifecyclePhase, list[LifecycleHook]] = {
            phase: [] for phase in STARTUP_PHASES
        }
        self._shutdown_hooks: dict[LifecyclePhase, list[LifecycleHook]] = {
            phase: [] for phase in SHUTDOWN_PHASES
        }
        self.started_at: datetime | None = None
        self.stopped_at: datetime | None = None

    @property
    def phase(self) -> LifecyclePhase:
        """Return the current lifecycle phase."""
        return self._phase

    @property
    def is_running(self) -> bool:
        """Return whether the application is running."""
        return self._phase is LifecyclePhase.RUNNING

    def register_startup_hook(self, phase: LifecyclePhase, hook: LifecycleHook) -> LifecycleManager:
        """Register a startup hook for a lifecycle phase."""
        if phase not in self._startup_hooks:
            raise InvalidLifecycleTransitionError(
                message=f"Phase '{phase.value}' is not a startup phase",
                details={"phase": phase.value},
            )
        self._startup_hooks[phase].append(hook)
        return self

    def register_shutdown_hook(self, phase: LifecyclePhase, hook: LifecycleHook) -> LifecycleManager:
        """Register a shutdown hook for a lifecycle phase."""
        if phase not in self._shutdown_hooks:
            raise InvalidLifecycleTransitionError(
                message=f"Phase '{phase.value}' is not a shutdown phase",
                details={"phase": phase.value},
            )
        self._shutdown_hooks[phase].append(hook)
        return self

    async def start(self) -> LifecyclePhase:
        """Run startup hooks in order and mark the application as running."""
        if self._phase is LifecyclePhase.RUNNING:
            return self._phase
        if self._phase not in {LifecyclePhase.BOOTSTRAP, LifecyclePhase.SHUTDOWN}:
            raise InvalidLifecycleTransitionError(
                message="Application can only start from bootstrap or shutdown",
                details={"current_phase": self._phase.value},
            )

        for phase in STARTUP_PHASES:
            await self._run_hooks(phase, self._startup_hooks[phase])

        self._phase = LifecyclePhase.RUNNING
        self.started_at = datetime.now(UTC)
        return self._phase

    async def stop(self) -> LifecyclePhase:
        """Run shutdown hooks in order and mark the application as stopped."""
        if self._phase is LifecyclePhase.SHUTDOWN:
            return self._phase
        if self._phase not in {LifecyclePhase.RUNNING, LifecyclePhase.SHUTTING_DOWN}:
            raise InvalidLifecycleTransitionError(
                message="Application can only stop from running or shutting_down",
                details={"current_phase": self._phase.value},
            )

        self._phase = LifecyclePhase.SHUTTING_DOWN
        for phase in SHUTDOWN_PHASES:
            await self._run_hooks(phase, self._shutdown_hooks[phase])

        self._phase = LifecyclePhase.SHUTDOWN
        self.stopped_at = datetime.now(UTC)
        return self._phase

    async def __aenter__(self) -> LifecycleManager:
        """Start the lifecycle when entering an async context."""
        await self.start()
        return self

    async def __aexit__(self, exc_type: object, exc: object, traceback: object) -> None:
        """Stop the lifecycle when exiting an async context."""
        await self.stop()

    async def _run_hooks(
        self,
        phase: LifecyclePhase,
        hooks: Sequence[LifecycleHook],
    ) -> None:
        """Execute hooks for a lifecycle phase."""
        for hook in hooks:
            result = hook()
            if inspect.isawaitable(result):
                await cast(Awaitable[None], result)


__all__ = ["LifecycleHook", "LifecycleManager"]
