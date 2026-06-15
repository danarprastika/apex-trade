from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.portfolio import Portfolio, PortfolioAllocation, PortfolioSnapshot
from app.database.repositories.base import BaseRepository


class PortfolioRepository(BaseRepository[Portfolio]):
    def __init__(self, db: Session):
        super().__init__(db, Portfolio)

    def get_by_user(self, user_id: str) -> Portfolio | None:
        return self.db.scalar(select(Portfolio).where(Portfolio.user_id == user_id))


class PortfolioAllocationRepository(BaseRepository[PortfolioAllocation]):
    def __init__(self, db: Session):
        super().__init__(db, PortfolioAllocation)


class PortfolioSnapshotRepository(BaseRepository[PortfolioSnapshot]):
    def __init__(self, db: Session):
        super().__init__(db, PortfolioSnapshot)

    def latest_for_portfolio(self, portfolio_id: str, limit: int = 100) -> list[PortfolioSnapshot]:
        return list(
            self.db.scalars(
                select(PortfolioSnapshot)
                .where(PortfolioSnapshot.portfolio_id == portfolio_id)
                .order_by(PortfolioSnapshot.captured_at.desc())
                .limit(limit)
            ).all()
        )
