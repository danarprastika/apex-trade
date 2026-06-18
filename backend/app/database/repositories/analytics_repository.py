from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.analytics import PerformanceMetrics
from app.database.repositories.base import BaseRepository


class PerformanceMetricsRepository(BaseRepository[PerformanceMetrics]):
    def __init__(self, db: Session):
        super().__init__(db, PerformanceMetrics)

    def get_by_portfolio_and_period(
        self,
        portfolio_id: str,
        period_start: datetime,
        period_end: datetime,
        period_type: str = "all",
    ) -> PerformanceMetrics | None:
        return self.db.scalar(
            select(PerformanceMetrics).where(
                (PerformanceMetrics.portfolio_id == portfolio_id)
                & (PerformanceMetrics.period_start == period_start)
                & (PerformanceMetrics.period_end == period_end)
                & (PerformanceMetrics.period_type == period_type)
            )
        )

    def get_latest_for_portfolio(
        self, portfolio_id: str, limit: int = 100
    ) -> list[PerformanceMetrics]:
        return list(
            self.db.scalars(
                select(PerformanceMetrics)
                .where(PerformanceMetrics.portfolio_id == portfolio_id)
                .order_by(PerformanceMetrics.period_start.desc())
                .limit(limit)
            ).all()
        )

    def get_by_user(
        self,
        user_id: str,
        period_type: str | None = None,
        limit: int = 100,
    ) -> list[PerformanceMetrics]:
        statement = select(PerformanceMetrics).where(
            PerformanceMetrics.user_id == user_id
        )
        if period_type:
            statement = statement.where(PerformanceMetrics.period_type == period_type)
        return list(
            self.db.scalars(
                statement.order_by(PerformanceMetrics.period_start.desc()).limit(limit)
            ).all()
        )

    def create_or_update(
        self,
        portfolio_id: str,
        user_id: str,
        period_start: datetime,
        period_end: datetime,
        period_type: str,
        metrics: dict[str, Any],
    ) -> PerformanceMetrics:
        existing = self.get_by_portfolio_and_period(
            portfolio_id, period_start, period_end, period_type
        )
        if existing:
            for key, value in metrics.items():
                setattr(existing, key, value)
            self.db.add(existing)
            return existing

        metrics_record = PerformanceMetrics(
            portfolio_id=portfolio_id,
            user_id=user_id,
            period_start=period_start,
            period_end=period_end,
            period_type=period_type,
            **metrics,
        )
        self.db.add(metrics_record)
        return metrics_record
