from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Exchange(Base, TimestampMixin):
    __tablename__ = "exchanges"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    exchange_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)

    accounts: Mapped[list[ExchangeAccount]] = relationship(back_populates="exchange")


class ExchangeAccount(Base, TimestampMixin):
    __tablename__ = "exchange_accounts"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    exchange_id: Mapped[str] = mapped_column(ForeignKey("exchanges.id"), index=True, nullable=False)
    api_key_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    api_secret_encrypted: Mapped[str] = mapped_column(String(512), nullable=False)
    is_testnet: Mapped[bool] = mapped_column(default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)
    sync_status: Mapped[str] = mapped_column(String(20), default="PENDING", nullable=False)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    balance_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    position_snapshot: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(2000), nullable=True)

    exchange: Mapped[Exchange] = relationship(back_populates="accounts")
