from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.trading import Order, Position, Signal, Strategy, StrategyParameter, Trade
from app.database.models.exchange import ExchangeAccount
from app.database.repositories.base import BaseRepository


class StrategyRepository(BaseRepository[Strategy]):
    def __init__(self, db: Session):
        super().__init__(db, Strategy)

    def get_by_code(self, code: str) -> Strategy | None:
        return self.db.scalar(select(Strategy).where(Strategy.code == code))


class StrategyParameterRepository(BaseRepository[StrategyParameter]):
    def __init__(self, db: Session):
        super().__init__(db, StrategyParameter)


class SignalRepository(BaseRepository[Signal]):
    def __init__(self, db: Session):
        super().__init__(db, Signal)

    def latest(self, limit: int = 100) -> list[Signal]:
        return list(
            self.db.scalars(select(Signal).order_by(Signal.signal_time.desc()).limit(limit)).all()
        )


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session):
        super().__init__(db, Order)

    def latest(self, limit: int = 100) -> list[Order]:
        return list(self.db.scalars(select(Order).order_by(Order.created_at.desc()).limit(limit)).all())

    def latest_by_user(self, user_id: str, limit: int = 100) -> list[Order]:
        return list(
            self.db.scalars(
                select(Order)
                .join(ExchangeAccount, Order.exchange_account_id == ExchangeAccount.id)
                .where(ExchangeAccount.user_id == user_id)
                .order_by(Order.created_at.desc())
                .limit(limit)
            ).all()
        )


class PositionRepository(BaseRepository[Position]):
    def __init__(self, db: Session):
        super().__init__(db, Position)

    def get_open(self, exchange_account_id: str, market_pair_id: str, strategy_id: str) -> Position | None:
        return self.db.scalar(
            select(Position).where(
                (Position.exchange_account_id == exchange_account_id)
                & (Position.market_pair_id == market_pair_id)
                & (Position.strategy_id == strategy_id)
                & (Position.status == "OPEN")
            )
        )


class TradeRepository(BaseRepository[Trade]):
    def __init__(self, db: Session):
        super().__init__(db, Trade)
