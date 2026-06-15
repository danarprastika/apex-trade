from __future__ import annotations

import logging

from app.database.models.exchange import Exchange
from app.database.repositories.exchange_repository import ExchangeRepository
from app.database.session import SessionLocal
from app.integrations.binance.client import BinanceClient
from app.services.market_service import MarketService
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="tasks.collectors.fetch_market_candles")
def fetch_market_candles(symbol: str, timeframe: str = "1h", limit: int = 100, exchange_id: str | None = None) -> dict[str, object]:
    db = SessionLocal()
    try:
        exchange = _get_or_create_exchange(db, exchange_id)
        market_service = MarketService(db)
        market_pair = market_service.get_or_create_market_pair(exchange.id, symbol)
        client = BinanceClient(testnet=True)
        candles = client.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)

        persisted = 0
        duplicates = 0
        for candle in candles:
            existing = market_service.candles.get_duplicate(market_pair.id, timeframe, candle.open_time)
            if existing:
                duplicates += 1
                continue
            market_service.upsert_candle(
                market_pair.id,
                timeframe,
                candle.open,
                candle.high,
                candle.low,
                candle.close,
                candle.volume,
                candle.open_time,
                candle.close_time,
            )
            persisted += 1

        logger.info("Fetched market candles symbol=%s timeframe=%s persisted=%s duplicates=%s", symbol, timeframe, persisted, duplicates)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "limit": limit,
            "exchange_id": exchange.id,
            "market_pair_id": market_pair.id,
            "fetched": len(candles),
            "persisted": persisted,
            "duplicates": duplicates,
            "status": "ok",
        }
    except Exception as exc:
        logger.exception("Market candle collection failed symbol=%s timeframe=%s", symbol, timeframe)
        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "limit": limit,
            "status": "error",
            "error": str(exc),
        }
    finally:
        db.close()


@celery_app.task(name="tasks.collectors.sync_exchange_accounts")
def sync_exchange_accounts(user_id: str) -> dict[str, str]:
    logger.info("Exchange account sync requested user_id=%s", user_id)
    return {"user_id": user_id, "status": "queued"}


def _get_or_create_exchange(db, exchange_id: str | None) -> Exchange:
    repositories = ExchangeRepository(db)
    if exchange_id:
        exchange = repositories.get(exchange_id)
        if exchange:
            return exchange
    exchange = repositories.create(name="Binance", exchange_type="SPOT", status="ACTIVE")
    repositories.commit()
    repositories.refresh(exchange)
    return exchange
