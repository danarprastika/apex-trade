from __future__ import annotations

import logging
from typing import Any

from app.events.types import ApexEvent

logger = logging.getLogger(__name__)


class SignalHandler:
    """Handles signal generation and validation events."""

    def __init__(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    async def signal_generated(self, strategy_id: str, signal: dict[str, Any], confidence: float, market_data: dict[str, Any]) -> None:
        event = ApexEvent(
            type="SIGNAL.GENERATED",
            payload={
                "strategy_id": strategy_id,
                "signal": signal,
                "confidence": confidence,
                "market_data": market_data,
            },
            source="signal-engine",
        )
        await self._event_bus.publish(event)

    async def signal_validated(self, signal_id: str, result: dict[str, Any]) -> None:
        event = ApexEvent(
            type="SIGNAL.VALIDATED",
            payload={"signal_id": signal_id, "validation_result": result},
            source="risk-engine",
        )
        await self._event_bus.publish(event)

    async def signal_rejected(self, signal_id: str, reason: str, veto_source: str) -> None:
        event = ApexEvent(
            type="SIGNAL.REJECTED",
            payload={"signal_id": signal_id, "reason": reason, "veto_source": veto_source},
            source="risk-engine",
            priority=1,
        )
        await self._event_bus.publish(event)