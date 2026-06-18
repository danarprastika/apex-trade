from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
from app.database.models.identity import User
from app.database.models.portfolio import Portfolio, PortfolioSnapshot
from app.database.models.trading import Position, Trade
from app.services.portfolio_analytics_service import PortfolioAnalyticsService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    db = SessionLocal()

    user = User(username="testuser", email="test@example.com", password_hash="hash", role="TRADER", status="ACTIVE")
    db.add(user)
    db.flush()

    portfolio = Portfolio(user_id=user.id, total_value=10000, cash_balance=10000, risk_score=0)

    db.add(portfolio)
    db.flush()
    db.commit()

    yield {"user": user, "portfolio": portfolio, "db": db}

    db.close()


def test_calculate_total_return(db_session):
    db = db_session["db"]
    portfolio = db_session["portfolio"]
    user = db_session["user"]

    now = datetime.now(UTC)

    snapshot1 = PortfolioSnapshot(
        portfolio_id=portfolio.id,
        total_value=10000.0,
        cash_balance=10000.0,
        open_positions=0,
        captured_at=now - timedelta(days=30),
    )
    snapshot2 = PortfolioSnapshot(
        portfolio_id=portfolio.id,
        total_value=11000.0,
        cash_balance=10000.0,
        open_positions=2,
        captured_at=now,
    )

    db.add_all([snapshot1, snapshot2])
    db.commit()

    service = PortfolioAnalyticsService(db)
    metrics = service.calculate_portfolio_analytics(
        portfolio_id=portfolio.id,
        user_id=user.id,
        date_from=snapshot1.captured_at,
        date_to=snapshot2.captured_at,
    )

    assert metrics.total_return == 0.1


def test_calculate_sharpe_ratio(db_session):
    db = db_session["db"]
    portfolio = db_session["portfolio"]
    user = db_session["user"]

    now = datetime.now(UTC)

    snapshots = []
    values = [10000, 10100, 10200, 10150, 10300]
    for i, val in enumerate(values):
        snapshots.append(
            PortfolioSnapshot(
                portfolio_id=portfolio.id,
                total_value=float(val),
                cash_balance=float(val),
                open_positions=0,
                captured_at=now - timedelta(days=len(values) - 1 - i),
            )
        )

    db.add_all(snapshots)
    db.commit()

    service = PortfolioAnalyticsService(db)
    metrics = service.calculate_portfolio_analytics(
        portfolio_id=portfolio.id,
        user_id=user.id,
        date_from=now - timedelta(days=4),
        date_to=now,
    )

    assert metrics.sharpe_ratio is not None
    assert isinstance(metrics.sharpe_ratio, float)


def test_calculate_profit_factor(db_session):
    db = db_session["db"]
    portfolio = db_session["portfolio"]
    user = db_session["user"]

    now = datetime.now(UTC)

    # Add snapshot for return metrics
    snapshot = PortfolioSnapshot(
        portfolio_id=portfolio.id,
        total_value=10000.0,
        cash_balance=10000.0,
        open_positions=1,
        captured_at=now,
    )
    db.add(snapshot)

    position = Position(
        exchange_account_id="dummy-account",
        market_pair_id="dummy-pair",
        strategy_id="dummy-strategy",
        portfolio_id=portfolio.id,
        entry_price=50000.0,
        quantity=1.0,
        current_price=50000.0,
        status="CLOSED",
        opened_at=datetime.now(UTC) - timedelta(days=1),
        closed_at=datetime.now(UTC),
    )

    db.add(position)
    db.flush()

    trade1 = Trade(
        position_id=position.id,
        strategy_id="dummy-strategy",
        entry_price=50000.0,
        exit_price=52000.0,
        quantity=1.0,
        net_profit=2000.0,
        opened_at=datetime.now(UTC) - timedelta(days=1),
        closed_at=datetime.now(UTC),
    )
    trade2 = Trade(
        position_id=position.id,
        strategy_id="dummy-strategy",
        entry_price=52000.0,
        exit_price=51000.0,
        quantity=1.0,
        net_profit=-1000.0,
        opened_at=datetime.now(UTC) - timedelta(hours=12),
        closed_at=datetime.now(UTC),
    )

    db.add_all([trade1, trade2])
    db.commit()

    service = PortfolioAnalyticsService(db)
    metrics = service.calculate_portfolio_analytics(
        portfolio_id=portfolio.id,
        user_id=user.id,
    )

    assert metrics.profit_factor == 2.0


def test_calculate_win_rate(db_session):
    db = db_session["db"]
    portfolio = db_session["portfolio"]
    user = db_session["user"]

    now = datetime.now(UTC)

    # Add snapshot for return metrics
    snapshot = PortfolioSnapshot(
        portfolio_id=portfolio.id,
        total_value=10000.0,
        cash_balance=10000.0,
        open_positions=1,
        captured_at=now,
    )
    db.add(snapshot)

    position = Position(
        exchange_account_id="dummy-account",
        market_pair_id="dummy-pair",
        strategy_id="dummy-strategy",
        portfolio_id=portfolio.id,
        entry_price=50000.0,
        quantity=1.0,
        current_price=50000.0,
        status="CLOSED",
        opened_at=datetime.now(UTC) - timedelta(days=2),
        closed_at=datetime.now(UTC),
    )

    db.add(position)
    db.flush()

    profits = [100, -50, 200, -25, 150]
    for i, profit in enumerate(profits):
        trade = Trade(
            position_id=position.id,
            strategy_id="dummy-strategy",
            entry_price=50000.0,
            exit_price=50000.0 + profit,
            quantity=1.0,
            net_profit=float(profit),
            opened_at=datetime.now(UTC) - timedelta(days=2 - i),
            closed_at=datetime.now(UTC),
        )
        db.add(trade)

    db.commit()

    service = PortfolioAnalyticsService(db)
    metrics = service.calculate_portfolio_analytics(
        portfolio_id=portfolio.id,
        user_id=user.id,
    )

    assert metrics.win_rate == 0.6


def test_calculate_max_drawdown(db_session):
    db = db_session["db"]
    portfolio = db_session["portfolio"]
    user = db_session["user"]

    now = datetime.now(UTC)

    snapshots = [
        PortfolioSnapshot(portfolio_id=portfolio.id, total_value=10000, cash_balance=10000, open_positions=0, captured_at=now - timedelta(days=3)),
        PortfolioSnapshot(portfolio_id=portfolio.id, total_value=11000, cash_balance=10000, open_positions=0, captured_at=now - timedelta(days=2)),
        PortfolioSnapshot(portfolio_id=portfolio.id, total_value=9000, cash_balance=10000, open_positions=0, captured_at=now - timedelta(days=1)),
        PortfolioSnapshot(portfolio_id=portfolio.id, total_value=10500, cash_balance=10000, open_positions=0, captured_at=now),
    ]

    db.add_all(snapshots)
    db.commit()

    service = PortfolioAnalyticsService(db)
    metrics = service.calculate_portfolio_analytics(
        portfolio_id=portfolio.id,
        user_id=user.id,
    )

    assert metrics.max_drawdown == pytest.approx(0.1818, rel=0.01)


def test_no_data_returns_null_metrics(db_session):
    db = db_session["db"]
    portfolio = db_session["portfolio"]
    user = db_session["user"]

    service = PortfolioAnalyticsService(db)
    metrics = service.calculate_portfolio_analytics(
        portfolio_id=portfolio.id,
        user_id=user.id,
    )

    assert metrics.total_return is None
    assert metrics.sharpe_ratio is None
    assert metrics.profit_factor is None
