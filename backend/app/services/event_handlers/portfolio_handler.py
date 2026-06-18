from __future__ import annotations

import logging
from typing import Any

from app.events.types import ApexEvent

logger = logging.getLogger(__name__)


class PortfolioHandler:
    """Handles portfolio and position events."""

    def __init__(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    async def position_opened(self, position_id: str, symbol: str, qty: float, entry_price: float) -> None:
        event = ApexEvent(
            type="POSITION.OPENED",
            payload={"position_id": position_id, "symbol": symbol, "qty": qty, "entry_price": entry_price},
            source="portfolio-engine",
        )
        await self._event_bus.publish(event)

    async def position_closed(self, position_id: str, exit_price: float, realized_pnl: float) -> None:
        event = ApexEvent(
            type="POSITION.CLOSED",
            payload={"position_id": position_id, "exit_price": exit_price, "realized_pnl": realized_pnl},
            source="portfolio-engine",
        )
        await self._event_bus.publish(event)