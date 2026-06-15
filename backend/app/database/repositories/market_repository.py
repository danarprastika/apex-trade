from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models.market import Asset, Candle, MarketPair
from app.database.repositories.base import BaseRepository


class AssetRepository(BaseRepository[Asset]):
    def __init__(self, db: Session):
        super().__init__(db, Asset)

    def get_by_symbol(self, symbol: str) -> Asset | None:
        return self.db.scalar(select(Asset).where(Asset.symbol == symbol))


class MarketPairRepository(BaseRepository[MarketPair]):
    def __init__(self, db: Session):
        super().__init__(db, MarketPair)

    def get_by_symbol(self, symbol: str) -> MarketPair | None:
        return self.db.scalar(select(MarketPair).where(MarketPair.symbol == symbol.upper()))

    def get_by_symbol_and_exchange(self, exchange_id: str, symbol: str) -> MarketPair | None:
        return self.db.scalar(
            select(MarketPair).where(
                (MarketPair.exchange_id == exchange_id) & (MarketPair.symbol == symbol)
            )
        )


class CandleRepository(BaseRepository[Candle]):
    def __init__(self, db: Session):
        super().__init__(db, Candle)

    def get_duplicate(
        self,
        market_pair_id: str,
        timeframe: str,
        open_time,
    ) -> Candle | None:
        return self.db.scalar(
            select(Candle).where(
                (Candle.market_pair_id == market_pair_id)
                & (Candle.timeframe == timeframe)
                & (Candle.open_time == open_time)
            )
        )

    def latest_for_pair(self, market_pair_id: str, timeframe: str, limit: int = 100):
        return list(
            self.db.scalars(
                select(Candle)
                .where((Candle.market_pair_id == market_pair_id) & (Candle.timeframe == timeframe))
                .order_by(Candle.open_time.desc())
                .limit(limit)
            ).all()
        )
