from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.domain.strategies.types import ConfigValidation, SignalResult


class StrategyPlugin(ABC):
    """Abstract base class for all strategy plugins."""

    @property
    @abstractmethod
    def metadata(self) -> Any:
        """Returns plugin metadata including name, version, type."""
        pass

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> None:
        """Initialize strategy with configuration parameters. Called once on load."""
        pass

    @abstractmethod
    def analyze(self, market_data: dict[str, Any]) -> SignalResult | None:
        """Analyze market data and produce trading signal if conditions met."""
        pass

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> ConfigValidation:
        """Validate configuration before initialization."""
        pass

    def on_market_update(self, market_data: dict[str, Any]) -> None:
        """Optional: Called for real-time bar-by-bar updates."""
        pass

    def on_signal_ack(self, signal_id: str) -> None:
        """Optional: Callback when signal is acknowledged by execution."""
        pass

    def get_parameters_schema(self) -> dict[str, Any]:
        """Returns JSON Schema for configuration validation."""
        return {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def get_state(self) -> dict[str, Any]:
        """Returns current internal state for debugging."""
        return {}

    def reset_state(self) -> None:
        """Reset internal state (useful for testing)."""
        pass