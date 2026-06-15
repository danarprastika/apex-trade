from __future__ import annotations

import logging
import re
from datetime import datetime

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.database.models.market import Asset, Candle, MarketPair
from app.database.repositories.market_repository import AssetRepository, CandleRepository, MarketPairRepository

logger = logging.getLogger(__name__)


class MarketService:
    def __init__(self, db: Session):
        self.db = db
        self.assets = AssetRepository(db)
        self.pairs = MarketPairRepository(db)
        self.candles = CandleRepository(db)

    def create_asset(self, symbol: str, asset_type: str, name: str | None = None) -> Asset:
        existing_asset = self.assets.get_by_symbol(symbol.upper())
        if existing_asset:
            raise ConflictError("Asset already exists")

        asset = self.assets.create(symbol=symbol.upper(), asset_type=asset_type.upper(), name=name)
        self.assets.commit()
        self.assets.refresh(asset)
        logger.info("Created asset asset_id=%s symbol=%s", asset.id, asset.symbol)
        return asset

    def get_or_create_asset(self, symbol: str, asset_type: str = "CRYPTO", name: str | None = None) -> Asset:
        existing_asset = self.assets.get_by_symbol(symbol.upper())
        if existing_asset:
            return existing_asset
        return self.create_asset(symbol, asset_type, name)

    def list_assets(self, limit: int = 100, offset: int = 0) -> list[Asset]:
        return self.assets.list(limit=limit, offset=offset)

    def create_market_pair(self, exchange_id: str, base_asset_id: str, quote_asset_id: str, symbol: str) -> MarketPair:
        existing_pair = self.pairs.get_by_symbol_and_exchange(exchange_id, symbol.upper())
        if existing_pair:
            raise ConflictError("Market pair already exists")
        if not self.assets.get(base_asset_id) or not self.assets.get(quote_asset_id):
            raise NotFoundError("Asset not found")

        pair = self.pairs.create(
            exchange_id=exchange_id,
            base_asset_id=base_asset_id,
            quote_asset_id=quote_asset_id,
            symbol=symbol.upper(),
        )
        self.pairs.commit()
        self.pairs.refresh(pair)
        logger.info("Created market pair pair_id=%s symbol=%s", pair.id, pair.symbol)
        return pair

    def get_or_create_market_pair(self, exchange_id: str, symbol: str) -> MarketPair:
        normalized_symbol = symbol.upper().replace("/", "").replace("-", "").replace("_", "")
        existing_pair = self.pairs.get_by_symbol_and_exchange(exchange_id, normalized_symbol)
        if existing_pair:
            return existing_pair

        base_symbol, quote_symbol = self._split_symbol(normalized_symbol)
        base_asset = self.get_or_create_asset(base_symbol)
        quote_asset = self.get_or_create_asset(quote_symbol)
        return self.create_market_pair(exchange_id, base_asset.id, quote_asset.id, normalized_symbol)

    def list_market_pairs(self, limit: int = 100, offset: int = 0) -> list[MarketPair]:
        return self.pairs.list(limit=limit, offset=offset)

    def create_candle(
        self,
        market_pair_id: str,
        timeframe: str,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        open_time: datetime,
        close_time: datetime,
    ) -> Candle:
        self._validate_candle(open, high, low, close, volume, open_time, close_time)

        duplicate = self.candles.get_duplicate(market_pair_id, timeframe, open_time)
        if duplicate:
            logger.info("Duplicate candle ignored pair_id=%s open_time=%s", market_pair_id, open_time)
            return duplicate

        candle = self.candles.create(
            market_pair_id=market_pair_id,
            timeframe=timeframe,
            open=open,
            high=high,
            low=low,
            close=close,
            volume=volume,
            open_time=open_time,
            close_time=close_time,
        )
        self.candles.commit()
        self.candles.refresh(candle)
        return candle

    def upsert_candle(
        self,
        market_pair_id: str,
        timeframe: str,
        open: float,
        high: float,
        low: float,
        close: float,
        volume: float,
        open_time: datetime,
        close_time: datetime,
    ) -> Candle:
        self._validate_candle(open, high, low, close, volume, open_time, close_time)
        duplicate = self.candles.get_duplicate(market_pair_id, timeframe, open_time)
        if duplicate:
            return duplicate
        return self.create_candle(market_pair_id, timeframe, open, high, low, close, volume, open_time, close_time)

    def list_candles(self, market_pair_id: str, timeframe: str, limit: int = 100) -> list[Candle]:
        return self.candles.latest_for_pair(market_pair_id, timeframe, limit=limit)

    @staticmethod
    def _split_symbol(symbol: str) -> tuple[str, str]:
        match = re.match(r"^([A-Z0-9]+)([A-Z0-9]{3,})$", symbol)
        if not match:
            raise ValidationError("Invalid market pair symbol")
        base = match.group(1)
        quote = match.group(2)
        if base in {"USDT", "USDC", "BUSD", "FDUSD", "TRY", "EUR", "GBP", "BTC", "ETH"} and len(base) >= 3:
            return base, quote
        for quote_candidate in ["USDT", "USDC", "BUSD", "FDUSD", "TRY", "EUR", "GBP", "BTC", "ETH"]:
            if symbol.endswith(quote_candidate) and len(symbol) > len(quote_candidate):
                return symbol[: -len(quote_candidate)], quote_candidate
        return base, quote

    @staticmethod
    def _validate_candle(open: float, high: float, low: float, close: float, volume: float, open_time: datetime, close_time: datetime) -> None:
        if close_time <= open_time:
            raise ValidationError("close_time must be after open_time")
        if high < max(open, close, low) or low > min(open, close, high):
            raise ValidationError("Invalid candle OHLC values")
        if volume < 0:
            raise ValidationError("Candle volume cannot be negative")
