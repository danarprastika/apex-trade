from __future__ import annotations

from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.backtest import BacktestConfig, BacktestMetric, BacktestRun, BacktestSession, BacktestTrade
from app.database.repositories.base import BaseRepository


class BacktestRunRepository(BaseRepository[BacktestRun]):
    def __init__(self, db: Session):
        super().__init__(db, BacktestRun)

    def list_by_user(self, user_id: str, limit: int = 100) -> list[BacktestRun]:
        return list(
            self.db.scalars(
                select(BacktestRun).where(BacktestRun.user_id == user_id).limit(limit).order_by(BacktestRun.created_at.desc())
            ).all()
        )

    def update_progress(self, run_id: str, progress: float, status: str | None = None) -> BacktestRun:
        run = self.get_or_raise(run_id, "Backtest run not found")
        run.progress = progress
        if status:
            run.status = status
        self.db.add(run)
        self.db.flush()
        return run


class BacktestConfigRepository(BaseRepository[BacktestConfig]):
    def __init__(self, db: Session):
        super().__init__(db, BacktestConfig)

    def list_by_strategy(self, strategy_id: str) -> list[BacktestConfig]:
        return list(
            self.db.scalars(
                select(BacktestConfig).where(BacktestConfig.strategy_id == strategy_id)
            ).all()
        )


class BacktestSessionRepository(BaseRepository[BacktestSession]):
    def __init__(self, db: Session):
        super().__init__(db, BacktestSession)

    def list_by_run(self, backtest_run_id: str) -> list[BacktestSession]:
        return list(
            self.db.scalars(
                select(BacktestSession).where(BacktestSession.backtest_run_id == backtest_run_id)
            ).all()
        )


class BacktestTradeRepository(BaseRepository[BacktestTrade]):
    def __init__(self, db: Session):
        super().__init__(db, BacktestTrade)

    def list_by_run(self, backtest_run_id: str) -> list[BacktestTrade]:
        return list(
            self.db.scalars(
                select(BacktestTrade)
                .where(BacktestTrade.backtest_run_id == backtest_run_id)
                .order_by(BacktestTrade.entry_time)
            ).all()
        )

    def list_closed_by_run(self, backtest_run_id: str) -> list[BacktestTrade]:
        return list(
            self.db.scalars(
                select(BacktestTrade)
                .where(BacktestTrade.backtest_run_id == backtest_run_id)
                .where(BacktestTrade.status == "CLOSED")
                .order_by(BacktestTrade.exit_time)
            ).all()
        )


class BacktestMetricRepository(BaseRepository[BacktestMetric]):
    def __init__(self, db: Session):
        super().__init__(db, BacktestMetric)

    def list_by_run(self, backtest_run_id: str) -> list[BacktestMetric]:
        return list(
            self.db.scalars(
                select(BacktestMetric).where(BacktestMetric.backtest_run_id == backtest_run_id)
            ).all()
        )

    def get_metric(self, backtest_run_id: str, metric_name: str) -> BacktestMetric | None:
        return self.db.scalar(
            select(BacktestMetric)
            .where(BacktestMetric.backtest_run_id == backtest_run_id)
            .where(BacktestMetric.metric_name == metric_name)
        )