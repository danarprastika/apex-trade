from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.portfolio import Portfolio, PortfolioAllocation, PortfolioSnapshot
from app.database.repositories.base import BaseRepository

__all__ = ["PortfolioRepository", "PortfolioAllocationRepository", "PortfolioSnapshotRepository"]


class PortfolioRepository(BaseRepository[Portfolio]):
    def __init__(self, db: Session):
        super().__init__(db, Portfolio)

    def get_by_user(self, user_id: str) -> Portfolio | None:
        result = self.db.execute(select(Portfolio).where(Portfolio.user_id == user_id))
        return result.scalar_one_or_none()


class PortfolioAllocationRepository(BaseRepository[PortfolioAllocation]):
    def __init__(self, db: Session):
        super().__init__(db, PortfolioAllocation)


class PortfolioSnapshotRepository(BaseRepository[PortfolioSnapshot]):
    def __init__(self, db: Session):
        super().__init__(db, PortfolioSnapshot)

    def latest_for_portfolio(self, portfolio_id: str, limit: int = 100) -> list[PortfolioSnapshot]:
        result = self.db.execute(
            select(PortfolioSnapshot)
            .where(PortfolioSnapshot.portfolio_id == portfolio_id)
            .order_by(PortfolioSnapshot.captured_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
