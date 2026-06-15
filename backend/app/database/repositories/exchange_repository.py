from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.exchange import Exchange, ExchangeAccount
from app.database.repositories.base import BaseRepository


class ExchangeRepository(BaseRepository[Exchange]):
    def __init__(self, db: Session):
        super().__init__(db, Exchange)

    def get_active(self, exchange_id: str) -> Exchange | None:
        return self.db.scalar(select(Exchange).where((Exchange.id == exchange_id) & (Exchange.status == "ACTIVE")))

    def get_by_name_and_type(self, name: str, exchange_type: str) -> Exchange | None:
        return self.db.scalar(
            select(Exchange).where((Exchange.name == name) & (Exchange.exchange_type == exchange_type))
        )


class ExchangeAccountRepository(BaseRepository[ExchangeAccount]):
    def __init__(self, db: Session):
        super().__init__(db, ExchangeAccount)

    def get_by_user_and_exchange(self, user_id: str, exchange_id: str) -> ExchangeAccount | None:
        return self.db.scalar(
            select(ExchangeAccount).where(
                (ExchangeAccount.user_id == user_id) & (ExchangeAccount.exchange_id == exchange_id)
            )
        )

    def list_by_user(self, user_id: str, limit: int = 100, offset: int = 0) -> list[ExchangeAccount]:
        return list(
            self.db.scalars(
                select(ExchangeAccount)
                .where(ExchangeAccount.user_id == user_id)
                .order_by(ExchangeAccount.created_at.desc())
                .limit(limit)
                .offset(offset)
            ).all()
        )

    def get_by_user(self, user_id: str, account_id: str) -> ExchangeAccount | None:
        return self.db.scalar(
            select(ExchangeAccount).where(
                (ExchangeAccount.id == account_id) & (ExchangeAccount.user_id == user_id)
            )
        )
