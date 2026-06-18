from __future__ import annotations

import logging
from time import perf_counter
from typing import Any

from app.domain.strategies.base import StrategyPlugin
from app.domain.strategies.types import PluginExecutionRecord, SignalResult

logger = logging.getLogger(__name__)


class StrategyEngine:
    """Orchestrates strategy plugin execution."""

    def __init__(self, registry: Any) -> None:
        self._registry = registry

    def analyze_symbol(
        self, symbol: str, timeframe: str, market_data: dict[str, Any]
    ) -> list[SignalResult]:
        """Run all active plugins against market data and collect signals."""
        signals: list[SignalResult] = []
        active_plugins = self._registry.get_active_plugins()

        for plugin in active_plugins:
            if not self._supports(plugin, symbol, timeframe):
                continue

            try:
                started_at = perf_counter()
                signal = plugin.analyze(market_data)
                duration_ms = (perf_counter() - started_at) * 1000
                if signal:
                    signals.append(signal)
                self._registry.record_execution(
                    PluginExecutionRecord(
                        code=plugin.metadata.name.lower().replace(" ", "_"),
                        success=True,
                        duration_ms=duration_ms,
                    )
                )
            except Exception as e:
                duration_ms = (perf_counter() - started_at) * 1000 if 'started_at' in locals() else 0.0
                self._registry.record_execution(
                    PluginExecutionRecord(
                        code=plugin.metadata.name.lower().replace(" ", "_"),
                        success=False,
                        duration_ms=duration_ms,
                        error=str(e),
                    )
                )
                logger.exception("Strategy plugin error code=%s", plugin.metadata.name)
                continue

        return signals

    def _supports(self, plugin: StrategyPlugin, symbol: str, timeframe: str) -> bool:
        metadata = plugin.metadata
        supported_assets = metadata.supported_assets
        supported_timeframes = metadata.supported_timeframes

        asset_supported = "*" in supported_assets or any(
            symbol.lower().startswith(a.lower()) for a in supported_assets
        )
        timeframe_supported = "*" in supported_timeframes or timeframe in supported_timeframes
        return asset_supported and timeframe_supported