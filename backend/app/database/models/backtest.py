from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class BacktestRun(Base, TimestampMixin):
    __tablename__ = "backtest_runs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"), index=True, nullable=False)
    config_id: Mapped[str] = mapped_column(ForeignKey("backtest_configs.id"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True, nullable=False)
    progress: Mapped[float] = mapped_column(Numeric(asdecimal=False), default=0, nullable=False)
    
    initial_capital: Mapped[float] = mapped_column(Numeric(asdecimal=False), nullable=False)
    final_capital: Mapped[float] = mapped_column(Numeric(asdecimal=False), nullable=True)
    total_trades: Mapped[int] = mapped_column(default=0, nullable=False)
    
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    end_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    error_details: Mapped[str] = mapped_column(Text, nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="backtest_runs")
    strategy: Mapped["Strategy"] = relationship(back_populates="backtest_runs")
    config: Mapped["BacktestConfig"] = relationship(back_populates="backtest_runs")
    sessions: Mapped[list["BacktestSession"]] = relationship(back_populates="backtest_run")
    trades: Mapped[list["BacktestTrade"]] = relationship(back_populates="backtest_run")
    metrics: Mapped[list["BacktestMetric"]] = relationship(back_populates="backtest_run")


class BacktestConfig(Base, TimestampMixin):
    __tablename__ = "backtest_configs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    position_sizing_method: Mapped[str] = mapped_column(String(20), default="FIXED", nullable=False)
    position_size_value: Mapped[float] = mapped_column(Numeric(asdecimal=False), nullable=False)
    max_positions: Mapped[int] = mapped_column(default=5, nullable=False)
    
    slippage_model: Mapped[dict] = mapped_column(JSON, nullable=False)
    commission_model: Mapped[dict] = mapped_column(JSON, nullable=False)
    
    strategy: Mapped["Strategy"] = relationship(back_populates="backtest_configs")
    backtest_runs: Mapped[list["BacktestRun"]] = relationship(back_populates="config")


class BacktestSession(Base, TimestampMixin):
    __tablename__ = "backtest_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    backtest_run_id: Mapped[str] = mapped_column(ForeignKey("backtest_runs.id"), index=True, nullable=False)
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), index=True, nullable=False)
    
    timeframe: Mapped[str] = mapped_column(String(10), nullable=False)
    candle_count: Mapped[int] = mapped_column(default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    
    start_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    end_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    backtest_run: Mapped["BacktestRun"] = relationship(back_populates="sessions")


class BacktestTrade(Base, TimestampMixin):
    __tablename__ = "backtest_trades"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    backtest_run_id: Mapped[str] = mapped_column(ForeignKey("backtest_runs.id"), index=True, nullable=False)
    backtest_session_id: Mapped[str] = mapped_column(ForeignKey("backtest_sessions.id"), index=True, nullable=False)
    signal_id: Mapped[str] = mapped_column(ForeignKey("signals.id"), index=True, nullable=True)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"), index=True, nullable=False)
    
    symbol: Mapped[str] = mapped_column(String(50), nullable=False)
    
    entry_price: Mapped[float] = mapped_column(Numeric(asdecimal=False), nullable=False)
    exit_price: Mapped[float] = mapped_column(Numeric(asdecimal=False), nullable=True)
    quantity: Mapped[float] = mapped_column(Numeric(asdecimal=False), nullable=False)
    
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    exit_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    gross_profit: Mapped[float] = mapped_column(Numeric(asdecimal=False), default=0, nullable=False)
    commission_cost: Mapped[float] = mapped_column(Numeric(asdecimal=False), default=0, nullable=False)
    slippage_cost: Mapped[float] = mapped_column(Numeric(asdecimal=False), default=0, nullable=False)
    net_profit: Mapped[float] = mapped_column(Numeric(asdecimal=False), default=0, nullable=False)
    
    status: Mapped[str] = mapped_column(String(20), default="OPEN", nullable=False)

    backtest_run: Mapped["BacktestRun"] = relationship(back_populates="trades")


class BacktestMetric(Base, TimestampMixin):
    __tablename__ = "backtest_metrics"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    backtest_run_id: Mapped[str] = mapped_column(ForeignKey("backtest_runs.id"), index=True, nullable=False)
    
    metric_name: Mapped[str] = mapped_column(String(50), nullable=False)
    metric_value: Mapped[float] = mapped_column(Numeric(asdecimal=False), nullable=False)
    metric_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    backtest_run: Mapped["BacktestRun"] = relationship(back_populates="metrics")