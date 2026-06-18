from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models.identity import User
from app.database.models.journal import TradeJournal
from app.database.repositories.journal_repository import (
    JournalEnrichmentRepository,
    TagRepository,
    TradeJournalRepository,
    TradeScreenshotRepository,
)
from app.schemas.journal import JournalFilterParams


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


def test_tag_repository_get_or_create(db_session):
    db = db_session["db"]

    repo = TagRepository(db)
    tag = repo.get_or_create("new-tag")

    assert tag.id is not None
    assert tag.name == "new-tag"
    assert tag.usage_count == 0


def test_tag_repository_increment_usage(db_session):
    db = db_session["db"]
    repo = TagRepository(db)
    tag = repo.get_or_create("test-tag")
    repo.increment_usage(tag)
    db.commit()
    db.refresh(tag)

    assert tag.usage_count == 1


def test_tag_repository_autocomplete(db_session):
    db = db_session["db"]
    repo = TagRepository(db)

    repo.get_or_create("alpha-tag")
    repo.get_or_create("beta-tag")
    repo.get_or_create("alpha-beta-tag")
    db.commit()

    results = repo.autocomplete("alpha", limit=10)
    assert len(results) == 2
    assert any(t.name == "alpha-tag" for t in results)


def test_tag_repository_get_by_names(db_session):
    db = db_session["db"]
    repo = TagRepository(db)

    repo.get_or_create("tag1")
    repo.get_or_create("tag2")
    repo.get_or_create("tag3")
    db.commit()

    results = repo.get_by_names(["tag1", "tag3"])
    assert len(results) == 2
    assert {t.name for t in results} == {"tag1", "tag3"}


def test_trade_journal_repository_create(db_session):
    db = db_session["db"]
    user = db_session["user"]

    repo = TradeJournalRepository(db)
    journal = repo.create(
        trade_id="trade-1",
        strategy_id="strategy-1",
        user_id=user.id,
        entry_reason="Test entry reason",
        exit_reason="Test exit reason",
        tags=[],
    )
    db.commit()

    assert journal.id is not None


def test_trade_journal_repository_get(db_session):
    db = db_session["db"]
    user = db_session["user"]

    repo = TradeJournalRepository(db)
    journal = repo.create(
        trade_id="trade-1",
        strategy_id="strategy-1",
        user_id=user.id,
        entry_reason="Test entry",
        exit_reason="Test exit",
        tags=[],
    )
    db.commit()

    fetched = repo.get(journal.id)
    assert fetched is not None


def test_trade_journal_repository_list_for_user(db_session):
    db = db_session["db"]
    user = db_session["user"]

    repo = TradeJournalRepository(db)
    for i in range(3):
        repo.create(
            trade_id=f"trade-{i}",
            strategy_id="strategy-1",
            user_id=user.id,
            entry_reason="Test entry",
            exit_reason="Test exit",
            tags=[],
            outcome="WIN" if i % 2 == 0 else "LOSS",
        )
    db.commit()

    journals, total = repo.list_for_user(user.id, JournalFilterParams())
    assert total == 3


def test_trade_screenshot_repository_create(db_session):
    db = db_session["db"]

    journal = TradeJournal(
        trade_id="trade-1",
        strategy_id="strategy-1",
        user_id="user-1",
        entry_reason="Test entry",
        exit_reason="Test exit",
        tags=[],
    )
    db.add(journal)
    db.flush()

    repo = TradeScreenshotRepository(db)
    screenshot = repo.create(
        trade_journal_id=journal.id,
        url="https://example.com/screenshot.png",
        caption="Test caption",
    )
    db.commit()

    assert screenshot.id is not None


def test_journal_enrichment_repository_create(db_session):
    db = db_session["db"]

    journal = TradeJournal(
        trade_id="trade-1",
        strategy_id="strategy-1",
        user_id="user-1",
        entry_reason="Test entry",
        exit_reason="Test exit",
        tags=[],
    )
    db.add(journal)
    db.flush()

    repo = JournalEnrichmentRepository(db)
    enrichment = repo.create(
        trade_journal_id=journal.id,
        enrichment_type="AUTO_TAGS",
        payload={"tags": ["winning-trade"]},
        confidence=0.85,
    )
    db.commit()

    assert enrichment.id is not None
