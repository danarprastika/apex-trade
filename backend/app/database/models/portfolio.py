from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class Portfolio(Base, TimestampMixin):
    __tablename__ = "portfolios"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    portfolio_name: Mapped[str] = mapped_column(String(100), default="Default", nullable=False)
    currency: Mapped[str] = mapped_column(String(20), default="USDT", nullable=False)
    total_value: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    cash_balance: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    risk_score: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)


class PortfolioAllocation(Base, TimestampMixin):
    __tablename__ = "portfolio_allocations"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True, nullable=False)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True, nullable=False)
    target_percentage: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    current_percentage: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True, nullable=False)
    total_value: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    cash_balance: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    open_positions: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_pnl: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    total_pnl: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(index=True, nullable=False)
