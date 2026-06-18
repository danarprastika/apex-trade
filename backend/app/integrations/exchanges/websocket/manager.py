from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

from app.events.bus import EventBus
from app.events.types import ApexEvent

from .base import BaseExchangeWebSocket
from .protocols import StreamCallback
from .types import StreamChannel, StreamMessage, WebSocketConfig

logger = logging.getLogger(__name__)

_EVENT_BUS_CALLBACKS: set[str] = set()


class WebSocketManager:
    def __init__(self, event_bus: EventBus | None = None, stream_prefix: str = "stream") -> None:
        self._exchanges: dict[str, BaseExchangeWebSocket] = {}
        self._callbacks: dict[str, list[StreamCallback]] = defaultdict(list)
        self._event_bus = event_bus
        self._stream_prefix = stream_prefix
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._running = False

    def add_exchange(self, exchange_id: str, adapter: Any) -> None:
        raise NotImplementedError(
            "Use add_exchange_ws(exchange_id, ws_adapter) instead. "
            "Pass a BaseExchangeWebSocket instance."
        )

    def add_exchange_ws(self, exchange_id: str, ws_adapter: BaseExchangeWebSocket) -> None:
        self._exchanges[exchange_id] = ws_adapter
        for channel, callback_list in self._callbacks.items():
            for callback in callback_list:
                ws_adapter.subscribe_callback(channel, callback)
        logger.info("Exchange added to WebSocket manager", exchange=exchange_id)

    def remove_exchange(self, exchange_id: str) -> None:
        if exchange_id in self._exchanges:
            ws = self._exchanges.pop(exchange_id)
            asyncio.ensure_future(ws.stop())
            if exchange_id in self._tasks:
                self._tasks.pop(exchange_id)
            logger.info("Exchange removed from WebSocket manager", exchange=exchange_id)

    async def start_stream(self, symbols: list[str], channels: list[StreamChannel | str]) -> None:
        self._running = True
        channel_names = [c.value if isinstance(c, StreamChannel) else c for c in channels]

        for exchange_id, ws in self._exchanges.items():
            for channel in channel_names:
                for symbol in symbols:
                    try:
                        await ws.subscribe(channel, symbol)
                        logger.debug(
                            "Subscription sent",
                            exchange=exchange_id,
                            channel=channel,
                            symbol=symbol,
                        )
                    except Exception:
                        logger.exception(
                            "Subscribe failed",
                            exchange=exchange_id,
                            channel=channel,
                            symbol=symbol,
                        )

            task = asyncio.ensure_future(self._run_exchange(ws))
            self._tasks[exchange_id] = task

        logger.info("WebSocket streaming started", exchanges=list(self._exchanges.keys()))

    async def stop_stream(self) -> None:
        self._running = False
        for exchange_id, task in list(self._tasks.items()):
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            ws = self._exchanges.get(exchange_id)
            if ws:
                await ws.stop()
        self._tasks.clear()
        logger.info("WebSocket streaming stopped")

    def subscribe_callback(self, channel: StreamChannel | str, callback: StreamCallback) -> None:
        channel_name = channel.value if isinstance(channel, StreamChannel) else channel
        self._callbacks[channel_name].append(callback)
        for ws in self._exchanges.values():
            ws.subscribe_callback(channel_name, callback)

    def unsubscribe_callback(self, channel: StreamChannel | str, callback: StreamCallback) -> None:
        channel_name = channel.value if isinstance(channel, StreamChannel) else channel
        if channel_name in self._callbacks:
            self._callbacks[channel_name] = [cb for cb in self._callbacks[channel_name] if cb != callback]
        for ws in self._exchanges.values():
            ws.unsubscribe_callback(channel_name, callback)

    async def _run_exchange(self, ws: BaseExchangeWebSocket) -> None:
        if not self._event_bus:
            await ws.start()
            return

        cb_key = f"{ws.exchange_id}:event_bus"
        if cb_key not in _EVENT_BUS_CALLBACKS:
            _EVENT_BUS_CALLBACKS.add(cb_key)
            for channel_name in list(ws.callbacks.keys()):
                ws.subscribe_callback(channel_name, self._create_event_bus_callback())

        await ws.start()

    def _create_event_bus_callback(self) -> StreamCallback:
        async def _publish(message: StreamMessage) -> None:
            await self._publish_to_event_bus(message)
        return _publish

    async def _publish_to_event_bus(self, message: StreamMessage) -> None:
        if not self._event_bus:
            return
        event_type = f"{self._stream_prefix}.{message.channel}".upper()
        event = ApexEvent(
            type=event_type,
            payload={
                "exchange_id": message.exchange_id,
                "channel": message.channel,
                "symbol": message.symbol,
                "data": message.data,
                "timestamp": message.timestamp.isoformat(),
            },
            source="websocket",
        )
        try:
            await self._event_bus.publish(event)
            if hasattr(self._event_bus, "publish_to_stream"):
                await self._event_bus.publish_to_stream(event, stream=f"{self._stream_prefix}:{message.channel}")
        except Exception:
            logger.exception("Failed to publish stream event to EventBus")
