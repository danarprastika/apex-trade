from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class PerformanceMetrics(Base, TimestampMixin):
    __tablename__ = "performance_metrics"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True, nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    period_start: Mapped[datetime] = mapped_column(index=True, nullable=False)
    period_end: Mapped[datetime] = mapped_column(index=True, nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)

    total_return: Mapped[float] = mapped_column(Numeric(20, 8), nullable=True)
    sharpe_ratio: Mapped[float] = mapped_column(Numeric(10, 6), nullable=True)
    sortino_ratio: Mapped[float] = mapped_column(Numeric(10, 6), nullable=True)
    calmar_ratio: Mapped[float] = mapped_column(Numeric(10, 6), nullable=True)
    profit_factor: Mapped[float] = mapped_column(Numeric(20, 8), nullable=True)
    win_rate: Mapped[float] = mapped_column(Numeric(5, 4), nullable=True)
    expectancy: Mapped[float] = mapped_column(Numeric(20, 8), nullable=True)
    max_drawdown: Mapped[float] = mapped_column(Numeric(20, 8), nullable=True)
    risk_adjusted_return: Mapped[float] = mapped_column(Numeric(20, 8), nullable=True)

    total_trades: Mapped[int] = mapped_column(nullable=True, default=0)
    winning_trades: Mapped[int] = mapped_column(nullable=True, default=0)
    losing_trades: Mapped[int] = mapped_column(nullable=True, default=0)
    gross_profit: Mapped[float] = mapped_column(Numeric(20, 8), nullable=True)
    gross_loss: Mapped[float] = mapped_column(Numeric(20, 8), nullable=True)
    volatility: Mapped[float] = mapped_column(Numeric(20, 8), nullable=True)
    downside_deviation: Mapped[float] = mapped_column(Numeric(20, 8), nullable=True)

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )