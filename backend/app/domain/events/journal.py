from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.events.trading import DomainEvent


@dataclass
class TradeJournalCreated(DomainEvent):
    def __init__(
        self,
        journal_id: str,
        user_id: str,
        trade_id: str,
        strategy_id: str,
        **kwargs: Any,
    ):
        super().__init__(
            type="TRADE_JOURNAL.CREATED",
            payload={
                "journal_id": journal_id,
                "user_id": user_id,
                "trade_id": trade_id,
                "strategy_id": strategy_id,
            },
            source="trade-journal-service",
            **kwargs,
        )


@dataclass
class TradeJournalUpdated(DomainEvent):
    def __init__(
        self,
        journal_id: str,
        user_id: str,
        trade_id: str,
        strategy_id: str,
        **kwargs: Any,
    ):
        super().__init__(
            type="TRADE_JOURNAL.UPDATED",
            payload={
                "journal_id": journal_id,
                "user_id": user_id,
                "trade_id": trade_id,
                "strategy_id": strategy_id,
            },
            source="trade-journal-service",
            **kwargs,
        )


@dataclass
class ScreenshotUploaded(DomainEvent):
    def __init__(self, journal_id: str, screenshot_id: str, user_id: str, **kwargs: Any):
        super().__init__(
            type="TRADE_JOURNAL.SCREENSHOT_UPLOADED",
            payload={
                "journal_id": journal_id,
                "screenshot_id": screenshot_id,
                "user_id": user_id,
            },
            source="trade-journal-service",
            **kwargs,
        )


__all__ = ["TradeJournalCreated", "TradeJournalUpdated", "ScreenshotUploaded"]
