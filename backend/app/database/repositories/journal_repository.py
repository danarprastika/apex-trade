from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.database.models.journal import (
    JournalEnrichment,
    Tag,
    TradeJournal,
    TradeScreenshot,
    TradeTagRelation,
)
from app.schemas.journal import JournalFilterParams
from app.services.journal_search_service import build_search_vector_filter

__all__ = [
    "TradeJournalRepository",
    "TradeScreenshotRepository",
    "TagRepository",
    "TradeTagRelationRepository",
    "JournalEnrichmentRepository",
]


class TradeJournalRepository:
    def __init__(self, db: Session):
        self.db = db

    def get(self, entity_id: Any) -> TradeJournal | None:
        return self.db.get(TradeJournal, entity_id)

    def get_or_raise(self, entity_id: Any, message: str) -> TradeJournal:
        entity = self.get(entity_id)
        if entity is None:
            raise ValueError(message)
        return entity

    def find_one(self, **filters: Any) -> TradeJournal | None:
        statement = select(TradeJournal)
        for key, value in filters.items():
            statement = statement.where(getattr(TradeJournal, key) == value)
        return self.db.scalar(statement)

    def find_many(self, **filters: Any) -> list[TradeJournal]:
        statement = select(TradeJournal)
        for key, value in filters.items():
            statement = statement.where(getattr(TradeJournal, key) == value)
        return list(self.db.scalars(statement).all())

    def create(self, **kwargs: Any) -> TradeJournal:
        journal = TradeJournal(**kwargs)
        self.db.add(journal)
        return journal

    def update(self, journal: TradeJournal, **kwargs: Any) -> TradeJournal:
        for key, value in kwargs.items():
            setattr(journal, key, value)
        self.db.add(journal)
        return journal

    def delete(self, journal: TradeJournal) -> None:
        self.db.delete(journal)

    def soft_delete(self, journal: TradeJournal) -> TradeJournal:
        journal.deleted_at = datetime.now()
        self.db.add(journal)
        return journal

    def commit(self) -> None:
        self.db.commit()

    def rollback(self) -> None:
        self.db.rollback()

    def refresh(self, entity: Any) -> Any:
        self.db.refresh(entity)
        return entity

    def _filtered_statement(
        self,
        user_id: str,
        filters: JournalFilterParams,
    ) -> Select[tuple[TradeJournal]]:
        statement = select(TradeJournal).where(
            (TradeJournal.user_id == user_id) & (TradeJournal.deleted_at.is_(None))
        )

        if filters.strategy_ids:
            statement = statement.where(TradeJournal.strategy_id.in_(filters.strategy_ids))
        if filters.outcome:
            statement = statement.where(TradeJournal.outcome.in_(filters.outcome))
        if filters.risk_score_range:
            statement = statement.where(
                TradeJournal.risk_score.between(filters.risk_score_range[0], filters.risk_score_range[1])
            )
        if filters.date_from:
            statement = statement.where(TradeJournal.created_at >= filters.date_from)
        if filters.date_to:
            statement = statement.where(TradeJournal.created_at <= filters.date_to)
        if filters.search:
            statement = statement.where(build_search_vector_filter(filters.search))

        if filters.tags:
            statement = statement.join(TradeTagRelation).join(Tag).where(Tag.name.in_(filters.tags)).distinct()

        return statement

    def list_for_user(
        self,
        user_id: str,
        filters: JournalFilterParams,
        paginate: bool = True,
    ) -> tuple[list[TradeJournal], int]:
        statement = self._filtered_statement(user_id, filters)
        total = 0

        if paginate:
            count_statement = select(func.count()).select_from(statement.order_by(None).subquery())
            total = int(self.db.scalar(count_statement) or 0)

        sort_column = getattr(TradeJournal, filters.sort_by)
        if filters.sort_order == "desc":
            statement = statement.order_by(sort_column.desc())
        else:
            statement = statement.order_by(sort_column.asc())

        if paginate:
            statement = statement.offset((filters.page - 1) * filters.size).limit(filters.size)

        journals = list(self.db.scalars(statement).all())
        return journals, total

    def list_for_user_all(
        self,
        user_id: str,
        filters: JournalFilterParams,
    ) -> list[TradeJournal]:
        journals, _ = self.list_for_user(user_id, filters, paginate=False)
        return journals

    def get_by_trade(self, trade_id: str) -> TradeJournal | None:
        return self.find_one(trade_id=trade_id, deleted_at=None)

    def search(self, user_id: str, query: str, limit: int = 20) -> list[TradeJournal]:
        statement = select(TradeJournal).where(
            (TradeJournal.user_id == user_id)
            & (TradeJournal.deleted_at.is_(None))
            & build_search_vector_filter(query)
        )
        statement = statement.order_by(TradeJournal.created_at.desc()).limit(limit)
        return list(self.db.scalars(statement).all())


class TradeScreenshotRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_for_journal(self, journal_id: str) -> list[TradeScreenshot]:
        statement = select(TradeScreenshot).where(TradeScreenshot.trade_journal_id == journal_id)
        return list(self.db.scalars(statement).all())

    def create(self, **kwargs: Any) -> TradeScreenshot:
        screenshot = TradeScreenshot(**kwargs)
        self.db.add(screenshot)
        return screenshot

    def get(self, screenshot_id: str) -> TradeScreenshot | None:
        return self.db.get(TradeScreenshot, screenshot_id)

    def delete(self, screenshot: TradeScreenshot) -> None:
        self.db.delete(screenshot)


class TagRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create(self, name: str) -> Tag:
        tag = self.db.scalar(select(Tag).where(Tag.name == name))
        if tag:
            return tag
        tag = Tag(name=name)
        self.db.add(tag)
        self.db.flush()
        self.db.refresh(tag)
        return tag

    def get_by_names(self, names: list[str]) -> list[Tag]:
        if not names:
            return []
        return list(self.db.scalars(select(Tag).where(Tag.name.in_(names))).all())

    def autocomplete(self, query: str, limit: int = 10) -> list[Tag]:
        cleaned = query.strip().lower()
        statement = select(Tag).order_by(Tag.usage_count.desc(), Tag.name.asc()).limit(limit)
        if cleaned:
            statement = statement.where(func.lower(Tag.name).contains(cleaned))
        return list(self.db.scalars(statement).all())

    def increment_usage(self, tag: Tag) -> None:
        tag.usage_count = tag.usage_count + 1
        self.db.add(tag)

    def decrement_usage(self, tag: Tag) -> None:
        tag.usage_count = max(tag.usage_count - 1, 0)
        self.db.add(tag)


class TradeTagRelationRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_relations(self, journal_id: str, tag_ids: list[str]) -> None:
        existing = set(self.find_tag_ids_for_journal(journal_id))
        relations = [
            TradeTagRelation(trade_journal_id=journal_id, tag_id=tag_id)
            for tag_id in tag_ids
            if tag_id not in existing
        ]
        if relations:
            self.db.add_all(relations)

    def remove_relations(self, journal_id: str, tag_ids: list[str]) -> None:
        if not tag_ids:
            return
        self.db.query(TradeTagRelation).filter(
            (TradeTagRelation.trade_journal_id == journal_id)
            & (TradeTagRelation.tag_id.in_(tag_ids))
        ).delete(synchronize_session=False)

    def find_tag_ids_for_journal(self, journal_id: str) -> list[str]:
        rows = (
            self.db.query(TradeTagRelation.tag_id)
            .filter(TradeTagRelation.trade_journal_id == journal_id)
            .all()
        )
        return [row.tag_id for row in rows]


class JournalEnrichmentRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, **kwargs: Any) -> JournalEnrichment:
        enrichment = JournalEnrichment(**kwargs)
        self.db.add(enrichment)
        return enrichment

    def list_for_journal(self, journal_id: str) -> list[JournalEnrichment]:
        return list(
            self.db.scalars(
                select(JournalEnrichment)
                .where(JournalEnrichment.trade_journal_id == journal_id)
                .order_by(JournalEnrichment.created_at.desc())
            ).all()
        )
