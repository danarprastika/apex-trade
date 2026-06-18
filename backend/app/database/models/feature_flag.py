from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, ForeignKey, JSON, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class FeatureFlag(Base, TimestampMixin):
    __tablename__ = "feature_flags"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    key: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    environment: Mapped[str] = mapped_column(String(20), nullable=False, default="development")
    owner: Mapped[str | None] = mapped_column(String(100), nullable=True)
    flag_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    is_kill_switch: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failure_mode: Mapped[str] = mapped_column(String(20), nullable=False, default="fail_closed")

    assignments: Mapped[list["FeatureFlagAssignment"]] = relationship(back_populates="flag", cascade="all, delete-orphan")
    audit_logs: Mapped[list["FeatureFlagAuditLog"]] = relationship(back_populates="flag", cascade="all, delete-orphan")


class FeatureFlagAssignment(Base, TimestampMixin):
    __tablename__ = "feature_flag_assignments"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    flag_id: Mapped[str] = mapped_column(ForeignKey("feature_flags.id", ondelete="CASCADE"), index=True, nullable=False)
    target_type: Mapped[str] = mapped_column(String(20), nullable=False)
    target_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    target_role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    rollout_percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    environment: Mapped[str | None] = mapped_column(String(20), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    flag_metadata: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)

    flag: Mapped[FeatureFlag] = relationship(back_populates="assignments")


class FeatureFlagAuditLog(Base):
    __tablename__ = "feature_flag_audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    flag_id: Mapped[str] = mapped_column(ForeignKey("feature_flags.id", ondelete="CASCADE"), index=True, nullable=False)
    flag_key: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    action: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    old_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    new_value: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    actor_user_id: Mapped[str | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True, nullable=True)
    actor_role: Mapped[str | None] = mapped_column(String(20), nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(100), nullable=True)
    reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), nullable=False)

    flag: Mapped[FeatureFlag] = relationship(back_populates="audit_logs")
