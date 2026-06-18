from __future__ import annotations

import asyncio
import logging
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Any

from ..base import BaseExchangeAdapter
from .protocols import StreamCallback
from .types import StreamChannel, StreamMessage, WebSocketConfig

logger = logging.getLogger(__name__)


class BaseExchangeWebSocket(ABC):
    def __init__(
        self,
        exchange_id: str,
        adapter: BaseExchangeAdapter,
        config: WebSocketConfig | None = None,
    ) -> None:
        self.exchange_id = exchange_id
        self.adapter = adapter
        self.config = config or WebSocketConfig()
        self.running = False
        self.callbacks: dict[str, list[StreamCallback]] = {channel.value: [] for channel in StreamChannel}
        self._reconnect_attempts = 0
        self._reconnect_delay = self.config.reconnect_interval

    def subscribe_callback(self, channel: StreamChannel | str, callback: StreamCallback) -> None:
        channel_name = channel.value if isinstance(channel, StreamChannel) else channel
        self.callbacks.setdefault(channel_name, []).append(callback)
        logger.debug("Callback subscribed", exchange=self.exchange_id, channel=channel_name)

    def unsubscribe_callback(self, channel: StreamChannel | str, callback: StreamCallback) -> None:
        channel_name = channel.value if isinstance(channel, StreamChannel) else channel
        if channel_name in self.callbacks:
            self.callbacks[channel_name] = [cb for cb in self.callbacks[channel_name] if cb != callback]

    async def _emit(self, message: StreamMessage) -> None:
        callbacks = self.callbacks.get(message.channel, [])
        for callback in callbacks:
            try:
                result = callback(message)
                if asyncio.iscoroutine(result):
                    await result
            except Exception:
                logger.exception("Callback error", exchange=self.exchange_id, channel=message.channel)

    @abstractmethod
    async def connect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def disconnect(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def subscribe(self, channel: str, symbol: str, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    async def unsubscribe(self, channel: str, symbol: str, **kwargs: Any) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _listen(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def _resubscribe(self) -> None:
        raise NotImplementedError

    async def _handle_disconnect(self) -> None:
        self.running = False
        if self._reconnect_attempts < self.config.max_reconnect_attempts:
            self._reconnect_attempts += 1
            delay = min(self._reconnect_delay * (self.config.backoff_factor ** (self._reconnect_attempts - 1)), self.config.backoff_max)
            logger.warning(
                "WebSocket disconnected, attempting reconnect",
                exchange=self.exchange_id,
                attempt=self._reconnect_attempts,
                delay=delay,
            )
            await asyncio.sleep(delay)
            try:
                await self.connect()
                self._reconnect_delay = self.config.reconnect_interval
                self._reconnect_attempts = 0
                await self._resubscribe()
            except Exception:
                logger.exception("Reconnect failed", exchange=self.exchange_id)
                await self._handle_disconnect()
        else:
            logger.error("Max reconnect attempts reached", exchange=self.exchange_id)

    async def start(self) -> None:
        self.running = True
        while self.running:
            try:
                await self.connect()
                self._reconnect_attempts = 0
                self._reconnect_delay = self.config.reconnect_interval
                await self._listen()
            except asyncio.CancelledError:
                self.running = False
                raise
            except Exception:
                logger.exception("WebSocket error", exchange=self.exchange_id)
                if self.running:
                    await self._handle_disconnect()

    async def stop(self) -> None:
        self.running = False
        await self.disconnect()
