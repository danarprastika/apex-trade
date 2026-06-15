from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class SystemMetric(Base):
    __tablename__ = "system_metrics"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    metric_name: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    metric_value: Mapped[float] = mapped_column(Numeric, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(index=True, nullable=False)


class SystemAlert(Base, TimestampMixin):
    __tablename__ = "system_alerts"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    alert_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    message: Mapped[str] = mapped_column(String(2000), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="OPEN", index=True, nullable=False)
    resolved_at: Mapped[datetime] = mapped_column(nullable=True)
