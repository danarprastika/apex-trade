from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.database.models.backtest import BacktestConfig, BacktestMetric, BacktestRun, BacktestSession, BacktestTrade
from app.database.models.trading import Strategy
from app.database.repositories.backtest_repository import (
    BacktestConfigRepository,
    BacktestMetricRepository,
    BacktestRunRepository,
    BacktestSessionRepository,
    BacktestTradeRepository,
)
from app.database.repositories.market_repository import CandleRepository
from app.database.repositories.trading_repository import StrategyRepository

logger = logging.getLogger(__name__)


class BacktestService:
    def __init__(self, db: Session):
        self.db = db
        self.runs = BacktestRunRepository(db)
        self.configs = BacktestConfigRepository(db)
        self.sessions = BacktestSessionRepository(db)
        self.trades = BacktestTradeRepository(db)
        self.metrics = BacktestMetricRepository(db)
        self.strategies = StrategyRepository(db)
        self.candles = CandleRepository(db)

    def create_run(
        self,
        user_id: str,
        strategy_id: str,
        name: str,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        config_id: str | None = None,
    ) -> BacktestRun:
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            raise NotFoundError("Strategy not found")

        if start_date is not None and end_date is not None and end_date <= start_date:
            raise ValidationError("Backtest end_date must be after start_date")
        if initial_capital <= 0:
            raise ValidationError("Backtest initial_capital must be greater than zero")

        run = self.runs.create(
            user_id=user_id,
            strategy_id=strategy_id,
            config_id=config_id,
            name=name,
            status="PENDING",
            progress=0.0,
            initial_capital=initial_capital,
            start_date=start_date,
            end_date=end_date,
        )
        self.runs.commit()
        self.runs.refresh(run)
        logger.info("Created backtest run run_id=%s strategy_id=%s", run.id, strategy_id)
        return run

    def create_config(
        self,
        strategy_id: str,
        name: str,
        position_sizing_method: str,
        position_size_value: float,
        max_positions: int,
        slippage_model: dict[str, Any],
        commission_model: dict[str, Any],
    ) -> BacktestConfig:
        strategy = self.strategies.get(strategy_id)
        if not strategy:
            raise NotFoundError("Strategy not found")

        if position_size_value <= 0:
            raise ValidationError("position_size_value must be greater than zero")
        if max_positions < 1:
            raise ValidationError("max_positions must be at least 1")

        config = self.configs.create(
            strategy_id=strategy_id,
            name=name,
            position_sizing_method=position_sizing_method,
            position_size_value=position_size_value,
            max_positions=max_positions,
            slippage_model=slippage_model,
            commission_model=commission_model,
        )
        self.configs.commit()
        self.configs.refresh(config)
        return config

    def get_run(self, run_id: str) -> BacktestRun:
        run = self.runs.get(run_id)
        if not run:
            raise NotFoundError("Backtest run not found")
        return run

    def list_runs(self, user_id: str, limit: int = 100) -> list[BacktestRun]:
        return self.runs.list_by_user(user_id, limit)

    def cancel_run(self, run_id: str) -> BacktestRun:
        run = self.get_run(run_id)
        if run.status not in {"PENDING", "RUNNING"}:
            raise ValidationError("Backtest run cannot be cancelled")
        run.status = "CANCELLED"
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def update_run_status(
        self, run_id: str, status: str, progress: float | None = None, error_details: str | None = None
    ) -> BacktestRun:
        run = self.get_run(run_id)
        run.status = status
        if progress is not None:
            run.progress = progress
        if error_details is not None:
            run.error_details = error_details
        if status in {"COMPLETED", "FAILED"}:
            run.completed_at = datetime.now(timezone.utc)
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def update(self, entity) -> None:
        self.db.add(entity)
        self.db.commit()
        self.db.refresh(entity)

    def add(self, entity) -> Any:
        self.db.add(entity)
        self.db.flush()
        return entity

    def add_session(
        self,
        backtest_run_id: str,
        market_pair_id: str,
        timeframe: str,
        start_time: datetime,
        end_time: datetime,
    ) -> BacktestSession:
        session = self.sessions.create(
            backtest_run_id=backtest_run_id,
            market_pair_id=market_pair_id,
            timeframe=timeframe,
            candle_count=0,
            status="PENDING",
            start_time=start_time,
            end_time=end_time,
        )
        self.sessions.commit()
        self.sessions.refresh(session)
        return session

    def add_trade(self, trade_data: dict[str, Any]) -> BacktestTrade:
        trade = self.trades.create(**trade_data)
        self.trades.commit()
        self.trades.refresh(trade)
        return trade

    def add_metric(
        self, backtest_run_id: str, metric_name: str, metric_value: float, metadata: dict[str, Any] | None = None
    ) -> BacktestMetric:
        metric = self.metrics.create(
            backtest_run_id=backtest_run_id,
            metric_name=metric_name,
            metric_value=metric_value,
            metric_metadata=metadata or {},
        )
        self.metrics.commit()
        self.metrics.refresh(metric)
        return metric