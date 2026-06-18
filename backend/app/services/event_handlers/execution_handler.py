from __future__ import annotations

import logging
from typing import Any

from app.events.types import ApexEvent

logger = logging.getLogger(__name__)


class ExecutionHandler:
    """Handles order and trade execution events."""

    def __init__(self, event_bus: Any) -> None:
        self._event_bus = event_bus

    async def order_created(self, order_id: str, signal_id: str | None, params: dict[str, Any]) -> None:
        event = ApexEvent(
            type="ORDER.CREATED",
            payload={"order_id": order_id, "signal_id": signal_id, "params": params},
            source="execution-engine",
        )
        await self._event_bus.publish(event)

    async def order_filled(self, order_id: str, fill_price: float, fill_qty: float) -> None:
        event = ApexEvent(
            type="ORDER.FILLED",
            payload={"order_id": order_id, "fill_price": fill_price, "fill_qty": fill_qty},
            source="execution-engine",
        )
        await self._event_bus.publish(event)

    async def trade_opened(self, trade_id: str, position_id: str, entry: dict[str, Any]) -> None:
        event = ApexEvent(
            type="TRADE.OPENED",
            payload={"trade_id": trade_id, "position_id": position_id, "entry": entry},
            source="execution-engine",
        )
        await self._event_bus.publish(event)

    async def trade_closed(self, trade_id: str, exit_price: float, realized_pnl: float) -> None:
        event = ApexEvent(
            type="TRADE.CLOSED",
            payload={"trade_id": trade_id, "exit_price": exit_price, "realized_pnl": realized_pnl},
            source="execution-engine",
        )
        await self._event_bus.publish(event)