from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.trading import Order, Position, Signal, Strategy, StrategyParameter, StrategyParameterSchema, Trade
from app.database.models.exchange import ExchangeAccount
from app.database.repositories.base import BaseRepository


class StrategyRepository(BaseRepository[Strategy]):
    def __init__(self, db: Session):
        super().__init__(db, Strategy)

    def get_by_code(self, code: str) -> Strategy | None:
        result = self.db.execute(select(Strategy).where(Strategy.code == code))
        return result.scalar_one_or_none()

    def find_by_type(self, strategy_type: str) -> list[Strategy]:
        result = self.db.execute(select(Strategy).where(Strategy.strategy_type == strategy_type))
        return list(result.scalars().all())


class StrategyParameterRepository(BaseRepository[StrategyParameter]):
    def __init__(self, db: Session):
        super().__init__(db, StrategyParameter)

    def find_by_strategy(self, strategy_id: str) -> list[StrategyParameter]:
        result = self.db.execute(
            select(StrategyParameter).where(StrategyParameter.strategy_id == strategy_id)
        )
        return list(result.scalars().all())

    def delete_by_strategy(self, strategy_id: str) -> None:
        parameters = self.find_by_strategy(strategy_id)
        for parameter in parameters:
            self.delete(parameter)


class StrategyParameterSchemaRepository(BaseRepository[StrategyParameterSchema]):
    def __init__(self, db: Session):
        super().__init__(db, StrategyParameterSchema)

    def get_active(self, strategy_id: str) -> StrategyParameterSchema | None:
        result = self.db.execute(
            select(StrategyParameterSchema).where(
                (StrategyParameterSchema.strategy_id == strategy_id)
                & (StrategyParameterSchema.is_active.is_(True))
            )
        )
        return result.scalar_one_or_none()

    def get_by_version(self, strategy_id: str, version: str) -> StrategyParameterSchema | None:
        result = self.db.execute(
            select(StrategyParameterSchema).where(
                (StrategyParameterSchema.strategy_id == strategy_id)
                & (StrategyParameterSchema.version == version)
            )
        )
        return result.scalar_one_or_none()

    def deactivate_previous(self, strategy_id: str) -> None:
        result = self.db.execute(
            select(StrategyParameterSchema).where(
                (StrategyParameterSchema.strategy_id == strategy_id)
                & (StrategyParameterSchema.is_active.is_(True))
            )
        )
        for schema in result.scalars().all():
            schema.is_active = False
            self.add(schema)


class SignalRepository(BaseRepository[Signal]):
    def __init__(self, db: Session):
        super().__init__(db, Signal)

    def latest(self, limit: int = 100) -> list[Signal]:
        result = self.db.execute(
            select(Signal).order_by(Signal.signal_time.desc()).limit(limit)
        )
        return list(result.scalars().all())


class OrderRepository(BaseRepository[Order]):
    def __init__(self, db: Session):
        super().__init__(db, Order)

    def latest(self, limit: int = 100) -> list[Order]:
        result = self.db.execute(
            select(Order).order_by(Order.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())

    def latest_by_user(self, user_id: str, limit: int = 100) -> list[Order]:
        result = self.db.execute(
            select(Order)
            .join(ExchangeAccount, Order.exchange_account_id == ExchangeAccount.id)
            .where(ExchangeAccount.user_id == user_id)
            .order_by(Order.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())


class PositionRepository(BaseRepository[Position]):
    def __init__(self, db: Session):
        super().__init__(db, Position)

    def get_open(self, exchange_account_id: str, market_pair_id: str, strategy_id: str) -> Position | None:
        result = self.db.execute(
            select(Position).where(
                (Position.exchange_account_id == exchange_account_id)
                & (Position.market_pair_id == market_pair_id)
                & (Position.strategy_id == strategy_id)
                & (Position.status == "OPEN")
            )
        )
        return result.scalar_one_or_none()


class TradeRepository(BaseRepository[Trade]):
    def __init__(self, db: Session):
        super().__init__(db, Trade)

    def get_by_position(self, position_id: str) -> Trade | None:
        result = self.db.execute(select(Trade).where(Trade.position_id == position_id))
        return result.scalar_one_or_none()
