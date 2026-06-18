from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models.identity import User
from app.schemas.journal import JournalFilterParams
from app.services.journal_analytics_service import JournalAnalyticsService


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


def test_performance_breakdown(db_session):
    db = db_session["db"]
    user = db_session["user"]

    service = JournalAnalyticsService(db)
    result = service.get_performance_breakdown(user.id, JournalFilterParams())

    assert "overall" in result
    assert "by_strategy" in result
    assert "by_risk_bucket" in result
    assert result["overall"]["total_trades"] == 0


def test_risk_correlation(db_session):
    db = db_session["db"]
    user = db_session["user"]

    service = JournalAnalyticsService(db)
    result = service.get_risk_correlation(user.id, JournalFilterParams())

    assert "correlation" in result
    assert "points" in result


def test_time_patterns(db_session):
    db = db_session["db"]
    user = db_session["user"]

    service = JournalAnalyticsService(db)
    result = service.get_time_patterns(user.id, JournalFilterParams())

    assert "by_hour" in result
    assert "by_day_of_week" in result


def test_tag_efficacy(db_session):
    db = db_session["db"]
    user = db_session["user"]

    service = JournalAnalyticsService(db)
    result = service.get_tag_efficacy(user.id, JournalFilterParams())

    assert "items" in result


def test_empty_journals(db_session):
    db = db_session["db"]
    user = db_session["user"]

    service = JournalAnalyticsService(db)
    result = service.get_performance_breakdown(user.id, JournalFilterParams())

    assert result["overall"]["total_trades"] == 0
