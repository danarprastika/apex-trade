from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base, TimestampMixin


class KillSwitchState(Base, TimestampMixin):
    __tablename__ = "kill_switch_states"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    scope: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    scope_id: Mapped[str] = mapped_column(String(100), nullable=True, index=True)
    enabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    reason: Mapped[str] = mapped_column(String(500), nullable=True)
    triggered_by: Mapped[str] = mapped_column(String(100), nullable=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class KillSwitchAuditLog(Base):
    __tablename__ = "kill_switch_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    scope: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    scope_id: Mapped[str] = mapped_column(String(100), nullable=True)
    action: Mapped[str] = mapped_column(String(20), nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_role: Mapped[str] = mapped_column(String(20), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(100), nullable=True)
    reason: Mapped[str] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)


class OrderReconciliationLog(Base, TimestampMixin):
    __tablename__ = "order_reconciliation_logs"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    order_id: Mapped[str] = mapped_column(ForeignKey("orders.id"), index=True, nullable=False)
    exchange_order_id: Mapped[str] = mapped_column(String(255), nullable=True)
    exchange_id: Mapped[str] = mapped_column(ForeignKey("exchanges.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    expected_status: Mapped[str] = mapped_column(String(20), nullable=True)
    actual_status: Mapped[str] = mapped_column(String(20), nullable=True)
    discrepancy_detected: Mapped[bool] = mapped_column(nullable=False, default=False)
    resolution_action: Mapped[str] = mapped_column(String(50), nullable=True)
    resolution_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class PositionReconciliationLog(Base, TimestampMixin):
    __tablename__ = "position_reconciliation_logs"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    position_id: Mapped[str] = mapped_column(ForeignKey("positions.id"), index=True, nullable=False)
    exchange_position_id: Mapped[str] = mapped_column(String(255), nullable=True)
    exchange_id: Mapped[str] = mapped_column(ForeignKey("exchanges.id"), nullable=False)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    expected_quantity: Mapped[float] = mapped_column(Numeric, nullable=True)
    actual_quantity: Mapped[float] = mapped_column(Numeric, nullable=True)
    quantity_discrepancy: Mapped[float] = mapped_column(Numeric, nullable=True)
    expected_entry_price: Mapped[float] = mapped_column(Numeric, nullable=True)
    actual_entry_price: Mapped[float] = mapped_column(Numeric, nullable=True)
    price_discrepancy: Mapped[float] = mapped_column(Numeric, nullable=True)
    discrepancy_detected: Mapped[bool] = mapped_column(nullable=False, default=False)
    resolution_action: Mapped[str] = mapped_column(String(50), nullable=True)
    resolution_details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class MarketDataQualityEvent(Base, TimestampMixin):
    __tablename__ = "market_data_quality_events"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), index=True, nullable=False)
    exchange_id: Mapped[str] = mapped_column(ForeignKey("exchanges.id"), nullable=False)
    data_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quality_score: Mapped[float] = mapped_column(Numeric(5, 4), nullable=True)
    issues: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    is_valid: Mapped[bool] = mapped_column(nullable=False, default=True)
    resolved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)


class ExposureLimit(Base, TimestampMixin):
    __tablename__ = "exposure_limits"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    exchange_id: Mapped[str] = mapped_column(ForeignKey("exchanges.id"), nullable=True)
    asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), nullable=True)
    max_exposure_percentage: Mapped[float] = mapped_column(Numeric, nullable=False)
    current_exposure_percentage: Mapped[float] = mapped_column(Numeric, nullable=False, default=0)
    scope: Mapped[str] = mapped_column(String(20), nullable=False)

    __table_args__ = (
        {"sqlite_autoincrement": True},
    )