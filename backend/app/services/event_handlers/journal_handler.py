from __future__ import annotations

import logging
from typing import Any

from app.domain.events.journal import ScreenshotUploaded, TradeJournalCreated, TradeJournalUpdated
from app.tasks.journal_enrichment import enrich_journal

logger = logging.getLogger(__name__)


class JournalEventHandler:
    def handle(self, event: Any) -> None:
        if isinstance(event, TradeJournalCreated | TradeJournalUpdated):
            self._enqueue_enrichment(event.payload["journal_id"])
        elif isinstance(event, ScreenshotUploaded):
            logger.info(
                "Screenshot uploaded screenshot_id=%s journal_id=%s",
                event.payload["screenshot_id"],
                event.payload["journal_id"],
            )

    def _enqueue_enrichment(self, journal_id: str) -> None:
        try:
            enrich_journal.delay(journal_id)
        except Exception:
            logger.exception("Failed to enqueue journal enrichment journal_id=%s", journal_id)
