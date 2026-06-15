from __future__ import annotations

from datetime import datetime
from uuid import uuid4

from sqlalchemy import BigInteger, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin


class Asset(Base, TimestampMixin):
    __tablename__ = "assets"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    symbol: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=True)
    asset_type: Mapped[str] = mapped_column(String(30), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)


class MarketPair(Base, TimestampMixin):
    __tablename__ = "market_pairs"

    id: Mapped[str] = mapped_column(primary_key=True, default=lambda: str(uuid4()))
    exchange_id: Mapped[str] = mapped_column(ForeignKey("exchanges.id"), index=True, nullable=False)
    base_asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), nullable=False)
    quote_asset_id: Mapped[str] = mapped_column(ForeignKey("assets.id"), nullable=False)
    symbol: Mapped[str] = mapped_column(String(50), index=True, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="ACTIVE", nullable=False)

    candles: Mapped[list[Candle]] = relationship(back_populates="market_pair")


class Candle(Base):
    __tablename__ = "candles"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), index=True, nullable=False)
    timeframe: Mapped[str] = mapped_column(String(10), index=True, nullable=False)
    open: Mapped[float] = mapped_column(Numeric, nullable=False)
    high: Mapped[float] = mapped_column(Numeric, nullable=False)
    low: Mapped[float] = mapped_column(Numeric, nullable=False)
    close: Mapped[float] = mapped_column(Numeric, nullable=False)
    volume: Mapped[float] = mapped_column(Numeric, nullable=False)
    open_time: Mapped[datetime] = mapped_column(index=True, nullable=False)
    close_time: Mapped[datetime] = mapped_column(nullable=False)

    market_pair: Mapped[MarketPair] = relationship(back_populates="candles")


class OrderBookSnapshot(Base):
    __tablename__ = "order_book_snapshots"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), index=True, nullable=False)
    bid_volume: Mapped[float] = mapped_column(Numeric, nullable=False)
    ask_volume: Mapped[float] = mapped_column(Numeric, nullable=False)
    spread: Mapped[float] = mapped_column(Numeric, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(index=True, nullable=False)


class FundingRate(Base):
    __tablename__ = "funding_rates"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), index=True, nullable=False)
    funding_rate: Mapped[float] = mapped_column(Numeric, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(index=True, nullable=False)


class OpenInterestRecord(Base):
    __tablename__ = "open_interest_records"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    market_pair_id: Mapped[str] = mapped_column(ForeignKey("market_pairs.id"), index=True, nullable=False)
    open_interest: Mapped[float] = mapped_column(Numeric, nullable=False)
    captured_at: Mapped[datetime] = mapped_column(index=True, nullable=False)
