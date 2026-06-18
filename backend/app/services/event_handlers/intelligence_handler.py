from __future__ import annotations

import logging
from datetime import datetime

from app.events.types import ApexEvent

logger = logging.getLogger(__name__)


class IntelligenceEventHandler:
    async def handle(self, event: ApexEvent) -> None:
        if event.type == "MARKET.REGIME_CHANGED":
            await self.on_regime_changed(event)
        elif event.type == "INTELLIGENCE.SNAPSHOT_UPDATED":
            await self.on_snapshot_updated(event)
        elif event.type == "INTELLIGENCE.ALERT_CREATED":
            await self.on_alert_created(event)
        elif event.type == "INTELLIGENCE.DATA_STALE":
            await self.on_data_stale(event)
        elif event.type == "NEWS.COLLECTED":
            await self.on_news_collected(event)
        elif event.type == "NEWS.EVENT_DETECTED":
            await self.on_news_event_detected(event)

    async def on_regime_changed(self, event: ApexEvent) -> None:
        logger.info(
            "Regime changed for pair=%s regime=%s confidence=%s",
            event.payload.get("market_pair_id"),
            event.payload.get("regime"),
            event.payload.get("confidence"),
        )

    async def on_snapshot_updated(self, event: ApexEvent) -> None:
        logger.info(
            "Intelligence snapshot updated for asset=%s score=%s",
            event.payload.get("asset_id"),
            event.payload.get("intelligence_score"),
        )

    async def on_alert_created(self, event: ApexEvent) -> None:
        logger.info(
            "Intelligence alert created type=%s severity=%s",
            event.payload.get("alert_type"),
            event.payload.get("severity"),
        )

    async def on_data_stale(self, event: ApexEvent) -> None:
        logger.warning(
            "Intelligence data stale scope=%s last_update=%s",
            event.payload.get("scope_type"),
            event.payload.get("last_update"),
        )

    async def on_news_collected(self, event: ApexEvent) -> None:
        logger.info(
            "News collected url=%s",
            event.payload.get("url"),
        )

    async def on_news_event_detected(self, event: ApexEvent) -> None:
        logger.info(
            "News event detected type=%s severity=%s",
            event.payload.get("event_type"),
            event.payload.get("severity"),
        )