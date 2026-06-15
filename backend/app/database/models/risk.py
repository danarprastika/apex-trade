from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class RiskProfile(Base, TimestampMixin):
    __tablename__ = "risk_profiles"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    max_risk_per_trade: Mapped[float] = mapped_column(Numeric, default=1.0, nullable=False)
    max_daily_loss: Mapped[float] = mapped_column(Numeric, default=3.0, nullable=False)
    max_drawdown: Mapped[float] = mapped_column(Numeric, default=15.0, nullable=False)
    max_open_positions: Mapped[int] = mapped_column(Integer, default=5, nullable=False)


class RiskEvent(Base, TimestampMixin):
    __tablename__ = "risk_events"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    description: Mapped[str] = mapped_column(String(2000), nullable=False)


class ExposureRecord(Base):
    __tablename__ = "exposure_records"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    portfolio_id: Mapped[str] = mapped_column(ForeignKey("portfolios.id"), index=True, nullable=False)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), index=True, nullable=False)
    exposure_percentage: Mapped[float] = mapped_column(Numeric, default=0, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(index=True, nullable=False)
