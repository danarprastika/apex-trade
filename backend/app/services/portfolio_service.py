from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.database.models.portfolio import Portfolio, PortfolioSnapshot
from app.database.repositories.portfolio_repository import PortfolioRepository, PortfolioSnapshotRepository

logger = logging.getLogger(__name__)


class PortfolioService:
    def __init__(self, db: Session):
        self.db = db
        self.portfolios = PortfolioRepository(db)
        self.snapshots = PortfolioSnapshotRepository(db)

    def get_or_create_default(self, user_id: str) -> Portfolio:
        portfolio = self.portfolios.get_by_user(user_id)
        if portfolio:
            return portfolio

        portfolio = self.portfolios.create(user_id=user_id, portfolio_name="Default", currency="USDT")
        self.portfolios.commit()
        self.portfolios.refresh(portfolio)
        logger.info("Created default portfolio portfolio_id=%s user_id=%s", portfolio.id, user_id)
        return portfolio

    def create(self, user_id: str, portfolio_name: str = "Default", currency: str = "USDT") -> Portfolio:
        portfolio = self.portfolios.create(user_id=user_id, portfolio_name=portfolio_name, currency=currency)
        self.portfolios.commit()
        self.portfolios.refresh(portfolio)
        logger.info("Created portfolio portfolio_id=%s user_id=%s", portfolio.id, user_id)
        return portfolio

    def get(self, portfolio_id: str) -> Portfolio:
        portfolio = self.portfolios.get(portfolio_id)
        if not portfolio:
            raise NotFoundError("Portfolio not found")
        return portfolio

    def snapshot(self, portfolio_id: str, total_value: float, cash_balance: float, open_positions: int = 0, daily_pnl: float = 0.0, total_pnl: float = 0.0) -> PortfolioSnapshot:
        portfolio = self.get(portfolio_id)
        portfolio.total_value = total_value
        portfolio.cash_balance = cash_balance
        snapshot = self.snapshots.create(
            portfolio_id=portfolio_id,
            total_value=total_value,
            cash_balance=cash_balance,
            open_positions=open_positions,
            daily_pnl=daily_pnl,
            total_pnl=total_pnl,
            captured_at=datetime.now(timezone.utc),
        )
        self.snapshots.commit()
        self.snapshots.refresh(snapshot)
        return snapshot

    def list_snapshots(self, portfolio_id: str, limit: int = 100) -> list[PortfolioSnapshot]:
        self.get(portfolio_id)
        return self.snapshots.latest_for_portfolio(portfolio_id, limit=limit)
