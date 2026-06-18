from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import JSON, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class TradeJournal(Base, TimestampMixin):
    __tablename__ = "trade_journals"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    trade_id: Mapped[str] = mapped_column(ForeignKey("trades.id"), nullable=False, unique=True)
    signal_id: Mapped[str | None] = mapped_column(ForeignKey("signals.id"), nullable=True)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    entry_reason: Mapped[str] = mapped_column(Text, nullable=False)
    exit_reason: Mapped[str] = mapped_column(Text, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    lessons_learned: Mapped[str | None] = mapped_column(Text, nullable=True)
    risk_score: Mapped[int | None] = mapped_column(nullable=True)
    outcome: Mapped[str | None] = mapped_column(String(20), index=True, nullable=True)
    tags: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    search_vector: Mapped[str | None] = mapped_column(
        "search_vector",
        nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(nullable=True, index=True)


class TradeScreenshot(Base, TimestampMixin):
    __tablename__ = "trade_screenshots"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    trade_journal_id: Mapped[str] = mapped_column(ForeignKey("trade_journals.id"), index=True, nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    caption: Mapped[str | None] = mapped_column(String(200), nullable=True)
    stage: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(default=0, nullable=False)


class Tag(Base, TimestampMixin):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    color: Mapped[str] = mapped_column(String(7), default="#6B7280", nullable=False)
    usage_count: Mapped[int] = mapped_column(default=0, nullable=False)


class TradeTagRelation(Base):
    __tablename__ = "trade_tag_relations"

    trade_journal_id: Mapped[str] = mapped_column(ForeignKey("trade_journals.id"), primary_key=True)
    tag_id: Mapped[str] = mapped_column(ForeignKey("tags.id"), primary_key=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(), nullable=False)


class JournalEnrichment(Base, TimestampMixin):
    __tablename__ = "journal_enrichments"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    trade_journal_id: Mapped[str] = mapped_column(ForeignKey("trade_journals.id"), index=True, nullable=False)
    enrichment_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Numeric, nullable=True)
