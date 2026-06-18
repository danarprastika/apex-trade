from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Strategy(Base, TimestampMixin):
    __tablename__ = "strategies"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    strategy_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="INACTIVE", index=True, nullable=False)

    backtest_configs: Mapped[list["BacktestConfig"]] = relationship(back_populates="strategy")
    backtest_runs: Mapped[list["BacktestRun"]] = relationship(back_populates="strategy")
    parameter_schemas: Mapped[list["StrategyParameterSchema"]] = relationship(back_populates="strategy")


class StrategyParameterSchema(Base, TimestampMixin):
    __tablename__ = "strategy_parameter_schemas"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"), index=True, nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    parameters_schema: Mapped[dict] = mapped_column(JSON, nullable=False)
    migrated_from: Mapped[str] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    strategy: Mapped["Strategy"] = relationship(back_populates="parameter_schemas")


class StrategyParameter(Base, TimestampMixin):
    __tablename__ = "strategy_parameters"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"), index=True, nullable=False)
    parameter_name: Mapped[str] = mapped_column(String(100), nullable=False)
    parameter_value: Mapped[str] = mapped_column(String(500), nullable=False)


class Signal(Base, TimestampMixin):
    __tablename__ = "signals"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"), index=True, nullable=False)
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), index=True, nullable=False)
    backtest_run_id: Mapped[str] = mapped_column(ForeignKey("backtest_runs.id"), index=True, nullable=True)
    signal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    confidence: Mapped[float] = mapped_column(Numeric, nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric, nullable=False)
    stop_loss: Mapped[float] = mapped_column(Numeric, nullable=True)
    take_profit: Mapped[float] = mapped_column(Numeric, nullable=True)
    reason: Mapped[str] = mapped_column(String(2000), nullable=False)
    signal_time: Mapped[datetime] = mapped_column(index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="PENDING", index=True, nullable=False)


class Order(Base, TimestampMixin):
    __tablename__ = "orders"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    exchange_account_id: Mapped[str] = mapped_column(ForeignKey("exchange_accounts.id"), index=True, nullable=False)
    signal_id: Mapped[str] = mapped_column(ForeignKey("signals.id"), index=True, nullable=True)
    exchange_order_id: Mapped[str] = mapped_column(String(255), index=True, nullable=True)
    order_type: Mapped[str] = mapped_column(String(20), nullable=False)
    side: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric, nullable=False)
    price: Mapped[float] = mapped_column(Numeric, nullable=True)
    filled_quantity: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="NEW", index=True, nullable=False)


class Position(Base, TimestampMixin):
    __tablename__ = "positions"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    exchange_account_id: Mapped[str] = mapped_column(ForeignKey("exchange_accounts.id"), index=True, nullable=False)
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), index=True, nullable=False)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"), index=True, nullable=False)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), nullable=True)
    entry_order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), nullable=True)
    entry_price: Mapped[float] = mapped_column(Numeric, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric, nullable=False)
    current_price: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    unrealized_pnl: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", index=True, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(index=True, nullable=False)
    closed_at: Mapped[datetime] = mapped_column(nullable=True)


class Trade(Base, TimestampMixin):
    __tablename__ = "trades"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    position_id: Mapped[str] = mapped_column(ForeignKey("positions.id"), nullable=False)
    strategy_id: Mapped[str] = mapped_column(ForeignKey("strategies.id"), index=True, nullable=False)
    entry_price: Mapped[float] = mapped_column(Numeric, nullable=False)
    exit_price: Mapped[float] = mapped_column(Numeric, nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric, nullable=False)
    gross_profit: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    net_profit: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    profit_percentage: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(default=0, nullable=False)
    opened_at: Mapped[datetime] = mapped_column(index=True, nullable=False)
    closed_at: Mapped[datetime] = mapped_column(index=True, nullable=False)
