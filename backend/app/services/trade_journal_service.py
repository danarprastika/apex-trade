from __future__ import annotations

import logging
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database.models.journal import (
    TradeJournal,
    TradeScreenshot,
)
from app.database.models.trading import Trade
from app.database.repositories.journal_repository import (
    JournalEnrichmentRepository,
    TagRepository,
    TradeJournalRepository,
    TradeScreenshotRepository,
    TradeTagRelationRepository,
)
from app.database.repositories.trading_repository import (
    StrategyRepository,
    TradeRepository,
)
from app.domain.events.journal import (
    ScreenshotUploaded,
    TradeJournalCreated,
    TradeJournalUpdated,
)
from app.schemas.journal import JournalFilterParams
from app.services.event_handlers.journal_handler import JournalEventHandler

logger = logging.getLogger(__name__)


class TradeJournalService:
    def __init__(self, db: Session):
        self.db = db
        self.journals = TradeJournalRepository(db)
        self.screenshots = TradeScreenshotRepository(db)
        self.tags = TagRepository(db)
        self.tag_relations = TradeTagRelationRepository(db)
        self.trades = TradeRepository(db)
        self.enrichments = JournalEnrichmentRepository(db)

    def _calculate_outcome(self, trade: Trade) -> str:
        if trade.net_profit > 0:
            return "WIN"
        if trade.net_profit < 0:
            return "LOSS"
        return "BREAK_EVEN"

    def _load_strategy_name(self, strategy_id: str) -> str:
        strategy_repo = StrategyRepository(self.db)
        strategy = strategy_repo.get(strategy_id)
        return strategy.name if strategy else ""

    def _attach_related(self, journal: TradeJournal):
        journal.tags = self.tags.get_by_names(journal.tags or [])
        journal.screenshots = self.screenshots.list_for_journal(journal.id)
        journal.strategy_name = self._load_strategy_name(journal.strategy_id)

    def attach_related(self, journal: TradeJournal) -> TradeJournal:
        self._attach_related(journal)
        return journal

    def _empty_statistics(self) -> dict[str, Any]:
        return {
            "total_trades": 0,
            "win_rate": None,
            "avg_risk_score": None,
            "avg_profit": None,
            "by_outcome": {},
            "by_strategy": {},
            "by_risk_score": {},
            "by_tag": {},
        }

    def _statistics_from_journals(self, journals: list[TradeJournal]) -> dict[str, Any]:
        if not journals:
            return self._empty_statistics()

        outcomes: dict[str, int] = {}
        strategies: dict[str, int] = {}
        risk_scores: dict[str, int] = {}
        tags: dict[str, int] = {}
        total_profit = 0.0
        risk_sum = 0.0
        risk_count = 0
        wins = 0

        for journal in journals:
            outcomes[journal.outcome or "UNKNOWN"] = outcomes.get(journal.outcome or "UNKNOWN", 0) + 1
            strategies[journal.strategy_id] = strategies.get(journal.strategy_id, 0) + 1
            if journal.risk_score:
                risk_scores[str(journal.risk_score)] = risk_scores.get(str(journal.risk_score), 0) + 1
                risk_sum += journal.risk_score
                risk_count += 1
            for tag in journal.tags or []:
                tags[tag.name] = tags.get(tag.name, 0) + 1

        for journal in journals:
            trade = self.trades.get(journal.trade_id)
            if trade:
                total_profit += trade.net_profit
                if trade.net_profit > 0:
                    wins += 1

        return {
            "total_trades": len(journals),
            "win_rate": wins / len(journals) if journals else None,
            "avg_risk_score": risk_sum / risk_count if risk_count else None,
            "avg_profit": total_profit / len(journals) if journals else None,
            "by_outcome": outcomes,
            "by_strategy": strategies,
            "by_risk_score": risk_scores,
            "by_tag": tags,
        }

    def _dispatch_event(self, event) -> None:
        try:
            JournalEventHandler().handle(event)
        except Exception:
            logger.exception("Failed to dispatch journal event event_type=%s", getattr(event, "type", None))

    def create(self, user_id: str, journal_data: Any) -> TradeJournal:
        trade = self.trades.get(journal_data.trade_id)
        if not trade:
            raise NotFoundError("Trade not found")

        journal = self.journals.create(
            trade_id=journal_data.trade_id,
            signal_id=None,
            strategy_id=trade.strategy_id,
            user_id=user_id,
            entry_reason=journal_data.entry_reason,
            exit_reason=journal_data.exit_reason,
            notes=journal_data.notes,
            lessons_learned=journal_data.lessons_learned,
            risk_score=journal_data.risk_score,
            outcome=self._calculate_outcome(trade),
            tags=[],
        )
        self.journals.commit()
        self.journals.refresh(journal)

        for name in {tag_name.strip() for tag_name in journal_data.tag_names if tag_name.strip()}:
            tag = self.tags.get_or_create(name)
            self.tags.increment_usage(tag)
            self.tag_relations.add_relations(journal.id, [tag.id])

        for url in journal_data.screenshot_urls:
            self.screenshots.create(
                trade_journal_id=journal.id,
                url=url,
                caption=None,
                stage="analysis",
                sort_order=0,
            )

        self.db.commit()
        self.db.refresh(journal)
        self._attach_related(journal)
        self._dispatch_event(
            TradeJournalCreated(
                journal_id=journal.id,
                user_id=user_id,
                trade_id=journal.trade_id,
                strategy_id=journal.strategy_id,
            )
        )
        logger.info("Created journal journal_id=%s trade_id=%s", journal.id, journal.trade_id)
        return journal

    def update(self, user_id: str, journal_id: str, journal_data: Any) -> TradeJournal:
        journal = self.journals.get(journal_id)
        if not journal or journal.deleted_at is not None:
            raise NotFoundError("Journal not found")
        if journal.user_id != user_id:
            raise NotFoundError("Journal not found")

        updates: dict[str, Any] = {}
        for field in ("entry_reason", "exit_reason", "notes", "lessons_learned", "risk_score"):
            value = getattr(journal_data, field, None)
            if value is not None:
                updates[field] = value

        if updates:
            self.journals.update(journal, **updates)

        if journal_data.add_tags:
            existing_tag_ids = set(self.tag_relations.find_tag_ids_for_journal(journal.id))
            for name in {tag_name.strip() for tag_name in journal_data.add_tags if tag_name.strip()}:
                tag = self.tags.get_or_create(name)
                self.tags.increment_usage(tag)
                if tag.id not in existing_tag_ids:
                    self.tag_relations.add_relations(journal.id, [tag.id])

        if journal_data.remove_tags:
            tags_to_remove = self.tags.get_by_names(
                [tag_name.strip() for tag_name in journal_data.remove_tags if tag_name.strip()]
            )
            tag_ids_to_remove = [tag.id for tag in tags_to_remove]
            self.tag_relations.remove_relations(journal.id, tag_ids_to_remove)
            for tag in tags_to_remove:
                self.tags.decrement_usage(tag)

        if journal_data.remove_screenshot_ids:
            for screenshot_id in journal_data.remove_screenshot_ids:
                screenshot = self.screenshots.get(screenshot_id)
                if screenshot and screenshot.trade_journal_id == journal.id:
                    self.screenshots.delete(screenshot)

        self.db.commit()
        self.db.refresh(journal)
        self._attach_related(journal)
        self._dispatch_event(
            TradeJournalUpdated(
                journal_id=journal.id,
                user_id=user_id,
                trade_id=journal.trade_id,
                strategy_id=journal.strategy_id,
            )
        )
        logger.info("Updated journal journal_id=%s", journal.id)
        return journal

    def get(self, user_id: str, journal_id: str) -> TradeJournal:
        journal = self.journals.get(journal_id)
        if not journal or journal.deleted_at is not None or journal.user_id != user_id:
            raise NotFoundError("Journal not found")
        self._attach_related(journal)
        return journal

    def list(self, user_id: str, filters: JournalFilterParams) -> tuple[list[TradeJournal], int]:
        journals, total = self.journals.list_for_user(user_id, filters)
        for journal in journals:
            self._attach_related(journal)
        return journals, total

    def delete(self, user_id: str, journal_id: str) -> None:
        journal = self.journals.get(journal_id)
        if not journal or journal.deleted_at is not None or journal.user_id != user_id:
            raise NotFoundError("Journal not found")
        self.journals.soft_delete(journal)
        self.journals.commit()
        logger.info("Soft-deleted journal journal_id=%s", journal_id)

    def add_screenshot(self, user_id: str, journal_id: str, url: str, caption: str | None, stage: str | None) -> TradeScreenshot:
        journal = self.journals.get(journal_id)
        if not journal or journal.deleted_at is not None or journal.user_id != user_id:
            raise NotFoundError("Journal not found")

        screenshot = self.screenshots.create(
            trade_journal_id=journal_id,
            url=url,
            caption=caption,
            stage=stage,
            sort_order=len(self.screenshots.list_for_journal(journal_id)),
        )
        self.journals.commit()
        self.journals.refresh(screenshot)
        self._dispatch_event(
            ScreenshotUploaded(
                journal_id=journal_id,
                screenshot_id=screenshot.id,
                user_id=user_id,
            )
        )
        logger.info("Added screenshot screenshot_id=%s journal_id=%s", screenshot.id, journal_id)
        return screenshot

    def remove_screenshot(self, user_id: str, journal_id: str, screenshot_id: str) -> None:
        journal = self.journals.get(journal_id)
        if not journal or journal.deleted_at is not None or journal.user_id != user_id:
            raise NotFoundError("Journal not found")

        screenshot = self.screenshots.get(screenshot_id)
        if not screenshot or screenshot.trade_journal_id != journal_id:
            raise NotFoundError("Screenshot not found")

        self.screenshots.delete(screenshot)
        self.journals.commit()
        logger.info("Removed screenshot screenshot_id=%s journal_id=%s", screenshot_id, journal_id)

    def bulk_tag(self, user_id: str, trade_ids: list[str], tag_names: list[str]) -> None:
        journals = []
        for trade_id in trade_ids:
            journal = self.journals.find_one(trade_id=trade_id, deleted_at=None)
            if not journal or journal.user_id != user_id:
                continue
            journals.append(journal)

        if not journals:
            raise NotFoundError("No journals found")

        tags = [self.tags.get_or_create(name) for name in {name.strip() for name in tag_names if name.strip()}]
        tag_ids = [tag.id for tag in tags]

        for journal in journals:
            existing_tag_ids = set(self.tag_relations.find_tag_ids_for_journal(journal.id))
            for tag_id in tag_ids:
                if tag_id not in existing_tag_ids:
                    self.tag_relations.add_relations(journal.id, [tag_id])
                    self.tags.increment_usage(next(tag for tag in tags if tag.id == tag_id))

        self.journals.commit()
        logger.info("Bulk tagged user_id=%s count=%d", user_id, len(journals))

    def get_statistics(self, user_id: str, filters: JournalFilterParams) -> dict[str, Any]:
        journals = self.journals.list_for_user_all(user_id, filters)
        for journal in journals:
            self._attach_related(journal)
        return self._statistics_from_journals(journals)

    def get_statistics_by_tag(self, user_id: str, filters: JournalFilterParams) -> dict[str, Any]:
        journals = self.journals.list_for_user_all(user_id, filters)
        for journal in journals:
            self._attach_related(journal)

        tag_names = sorted({tag.name for journal in journals for tag in journal.tags or []})
        return {
            tag: self._statistics_from_journals(
                [journal for journal in journals if any(existing.name == tag for existing in journal.tags or [])]
            )
            for tag in tag_names
        }

    def export_rows(self, user_id: str, filters: JournalFilterParams) -> list[dict[str, Any]]:
        journals = self.journals.list_for_user_all(user_id, filters)
        rows: list[dict[str, Any]] = []

        for journal in journals:
            self._attach_related(journal)
            trade = self.trades.get(journal.trade_id)
            rows.append(
                {
                    "journal_id": journal.id,
                    "trade_id": journal.trade_id,
                    "strategy_id": journal.strategy_id,
                    "strategy_name": journal.strategy_name,
                    "entry_reason": journal.entry_reason,
                    "exit_reason": journal.exit_reason,
                    "notes": journal.notes or "",
                    "lessons_learned": journal.lessons_learned or "",
                    "risk_score": journal.risk_score or "",
                    "outcome": journal.outcome or "",
                    "tags": ";".join(tag.name for tag in journal.tags or []),
                    "net_profit": trade.net_profit if trade else "",
                    "opened_at": trade.opened_at if trade else "",
                    "closed_at": trade.closed_at if trade else "",
                    "created_at": journal.created_at,
                }
            )

        return rows
