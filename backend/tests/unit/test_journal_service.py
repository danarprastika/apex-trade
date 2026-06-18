from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.core.exceptions import NotFoundError
from app.database.base import Base
from app.database.models.identity import User
from app.schemas.journal import (
    JournalFilterParams,
    TradeJournalCreate,
)
from app.services.trade_journal_service import TradeJournalService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    user = User(username="testuser", email="test@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
    db.add(user)
    db.flush()
    db.commit()

    yield {"user": user, "db": db}

    db.close()


def test_create_journal_entry(db_session):
    db = db_session["db"]
    user = db_session["user"]

    service = TradeJournalService(db)
    payload = TradeJournalCreate(
        trade_id="trade-1",
        entry_reason="Test entry reason",
        exit_reason="Test exit reason",
        risk_score=5,
    )

    with pytest.raises(NotFoundError):
        service.create(user.id, payload)


def test_create_journal_entry_not_found_trade(db_session):
    db = db_session["db"]
    user = db_session["user"]

    service = TradeJournalService(db)
    payload = TradeJournalCreate(
        trade_id="nonexistent-trade",
        entry_reason="Test entry reason",
        exit_reason="Test exit reason",
    )

    with pytest.raises(NotFoundError):
        service.create(user.id, payload)


def test_get_journal_entry_not_found(db_session):
    db = db_session["db"]
    user = db_session["user"]

    service = TradeJournalService(db)

    with pytest.raises(NotFoundError):
        service.get(user.id, "nonexistent-id")


def test_list_journals(db_session):
    db = db_session["db"]
    user = db_session["user"]

    service = TradeJournalService(db)
    journals, total = service.list(user.id, JournalFilterParams())
    assert total == 0


def test_get_statistics(db_session):
    db = db_session["db"]
    user = db_session["user"]

    service = TradeJournalService(db)
    stats = service.get_statistics(user.id, JournalFilterParams())
    assert stats["total_trades"] == 0


def test_delete_journal_entry(db_session):
    db = db_session["db"]
    user = db_session["user"]

    service = TradeJournalService(db)
    journals = service.journals.find_many(user_id=user.id)
    assert len(journals) == 0
