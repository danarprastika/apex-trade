from __future__ import annotations

import logging
from typing import Any

from app.events.types import ApexEvent

logger = logging.getLogger(__name__)


class AIHandler:
    """Handles AI module events."""

    def __init__(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    async def prediction_made(self, prediction_id: str, asset: str, value: float, confidence: float) -> None:
        event = ApexEvent(
            type="AI.PREDICTION_MADE",
            payload={
                "prediction_id": prediction_id,
                "asset": asset,
                "value": value,
                "confidence": confidence,
            },
            source="ai-module",
        )
        await self._event_bus.publish(event)

    async def learning_triggered(self, source_event: str, feature_importance: dict[str, float]) -> None:
        event = ApexEvent(
            type="AI.LEARNING_TRIGGERED",
            payload={"source_event": source_event, "feature_importance": feature_importance},
            source="ai-module",
        )
        await self._event_bus.publish(event)

    async def decision_made(self, decision_id: str, recommendation: str, reasoning: str) -> None:
        event = ApexEvent(
            type="AI.DECISION_MADE",
            payload={"decision_id": decision_id, "recommendation": recommendation, "reasoning": reasoning},
            source="ai-module",
        )
        await self._event_bus.publish(event)