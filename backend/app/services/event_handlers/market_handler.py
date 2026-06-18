from __future__ import annotations

import logging
from typing import Any

from app.events.types import ApexEvent

logger = logging.getLogger(__name__)


class MarketDataHandler:
    """Handles market data events for market collector."""

    def __init__(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    async def on_price_update(self, symbol: str, price: float, exchange: str) -> None:
        from app.events.types import ApexEvent
        event = ApexEvent(
            type="MARKET.PRICE_UPDATED",
            payload={"symbol": symbol, "price": price, "exchange": exchange},
            source="market-collector",
        )
        await self._event_bus.publish(event)

    async def on_candle_closed(self, symbol: str, timeframe: str, candle: dict[str, Any]) -> None:
        event = ApexEvent(
            type="MARKET.CANDLE_CLOSED",
            payload={"symbol": symbol, "timeframe": timeframe, "candle": candle},
            source="market-collector",
        )
        await self._event_bus.publish(event)