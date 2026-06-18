from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from app.domain.entities.strategy import StrategyType
from app.domain.strategies.base import StrategyPlugin
from app.domain.strategies.types import (
    PluginExecutionRecord,
    PluginHealthSnapshot,
    PluginHealthStatus,
    PluginLifecycleState,
)

logger = logging.getLogger(__name__)


class PluginRegistry:
    """Centralized registry for strategy plugins."""

    def __init__(self) -> None:
        self._plugins: dict[str, StrategyPlugin] = {}
        self._by_type: dict[str, list[str]] = {}
        self._active_plugins: set[str] = set()
        self._lifecycle: dict[str, PluginLifecycleState] = {}
        self._health: dict[str, PluginHealthSnapshot] = {}

    def register(self, plugin: StrategyPlugin) -> None:
        metadata = plugin.metadata
        code = metadata.name.lower().replace(" ", "_")
        strategy_type = StrategyType(metadata.strategy_type).value
        self._plugins[code] = plugin
        self._lifecycle[code] = PluginLifecycleState.registered
        self._health[code] = PluginHealthSnapshot(
            code=code,
            lifecycle_state=PluginLifecycleState.registered,
            health_status=PluginHealthStatus.unknown,
        )
        if strategy_type not in self._by_type:
            self._by_type[strategy_type] = []
        if code not in self._by_type[strategy_type]:
            self._by_type[strategy_type].append(code)
        logger.info("Registered strategy plugin code=%s type=%s", code, strategy_type)

    def unregister(self, code: str) -> None:
        if code in self._plugins:
            plugin = self._plugins[code]
            strategy_type = StrategyType(plugin.metadata.strategy_type).value
            del self._plugins[code]
            if strategy_type in self._by_type:
                self._by_type[strategy_type] = [
                    c for c in self._by_type[strategy_type] if c != code
                ]
            self._active_plugins.discard(code)
            self._mark_lifecycle(code, PluginLifecycleState.unregistered)
            logger.info("Unregistered strategy plugin code=%s", code)

    def get_plugin(self, code: str) -> StrategyPlugin | None:
        return self._plugins.get(code)

    def get_plugin_codes(self) -> list[str]:
        return list(self._plugins.keys())

    def get_plugins_by_type(self, strategy_type: str) -> list[StrategyPlugin]:
        normalized_strategy_type = StrategyType(strategy_type).value
        codes = self._by_type.get(normalized_strategy_type, [])
        return [self._plugins[code] for code in codes if code in self._plugins]

    def activate(self, code: str) -> None:
        if code in self._plugins:
            self._active_plugins.add(code)
            self._mark_lifecycle(code, PluginLifecycleState.activated)
            self._mark_healthy(code)
            logger.info("Activated strategy plugin code=%s", code)
        else:
            raise ValueError(f"Plugin not found: {code}")

    def deactivate(self, code: str) -> None:
        self._active_plugins.discard(code)
        self._mark_lifecycle(code, PluginLifecycleState.deactivated)
        logger.info("Deactivated strategy plugin code=%s", code)

    def is_active(self, code: str) -> bool:
        return code in self._active_plugins

    def get_active_plugins(self) -> list[StrategyPlugin]:
        return [self._plugins[code] for code in self._active_plugins if code in self._plugins]

    def get_active_codes(self) -> list[str]:
        return list(self._active_plugins)

    def mark_discovered(self, code: str) -> None:
        self._mark_lifecycle(code, PluginLifecycleState.discovered)

    def mark_validated(self, code: str) -> None:
        self._mark_lifecycle(code, PluginLifecycleState.validated)

    def mark_loaded(self, code: str) -> None:
        self._mark_lifecycle(code, PluginLifecycleState.loaded)

    def mark_initialized(self, code: str) -> None:
        self._mark_lifecycle(code, PluginLifecycleState.initialized)

    def mark_failed(self, code: str, error: str) -> None:
        snapshot = self._health.setdefault(
            code,
            PluginHealthSnapshot(
                code=code,
                lifecycle_state=PluginLifecycleState.failed,
                health_status=PluginHealthStatus.unhealthy,
            ),
        )
        snapshot.lifecycle_state = PluginLifecycleState.failed
        snapshot.health_status = PluginHealthStatus.unhealthy
        snapshot.last_error = error
        snapshot.updated_at = datetime.now(timezone.utc)
        logger.error("Strategy plugin failed code=%s error=%s", code, error)

    def record_execution(self, record: PluginExecutionRecord) -> None:
        snapshot = self._health.setdefault(
            record.code,
            PluginHealthSnapshot(
                code=record.code,
                lifecycle_state=PluginLifecycleState.activated,
                health_status=PluginHealthStatus.unknown,
            ),
        )
        snapshot.executions += 1
        snapshot.last_execution_ms = record.duration_ms
        snapshot.last_execution_at = datetime.now(timezone.utc)
        if record.success:
            snapshot.failures = 0
            snapshot.health_status = PluginHealthStatus.healthy
        else:
            snapshot.failures += 1
            snapshot.last_error = record.error
            snapshot.health_status = PluginHealthStatus.degraded if snapshot.failures < 3 else PluginHealthStatus.unhealthy
        snapshot.updated_at = datetime.now(timezone.utc)

    def get_health(self, code: str) -> PluginHealthSnapshot | None:
        return self._health.get(code)

    def get_health_summary(self) -> dict[str, PluginHealthSnapshot]:
        return dict(self._health)

    def _mark_lifecycle(self, code: str, state: PluginLifecycleState) -> None:
        if code in self._health:
            self._health[code].lifecycle_state = state
            self._health[code].updated_at = datetime.now(timezone.utc)
        self._lifecycle[code] = state

    def _mark_healthy(self, code: str) -> None:
        if code in self._health:
            self._health[code].health_status = PluginHealthStatus.healthy
            self._health[code].updated_at = datetime.now(timezone.utc)

    def get_plugin_by_strategy(self, strategy_id: str) -> StrategyPlugin | None:
        for plugin in self._plugins.values():
            if plugin.metadata.strategy_id == strategy_id:
                return plugin
        return None