from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from ..base import BaseExchangeAdapter
from .base import BaseExchangeWebSocket
from .types import StreamChannel, StreamMessage, WebSocketConfig

logger = logging.getLogger(__name__)

BINANCE_WS_MAINNET = "wss://stream.binance.com:9443/ws"
BINANCE_WS_TESTNET = "wss://testnet.binance.vision/ws"

_CHANNEL_MAP: dict[StreamChannel, str] = {
    StreamChannel.TICKER: "@ticker",
    StreamChannel.CANDLES: "@kline",
    StreamChannel.ORDER_BOOK: "@depth",
    StreamChannel.TRADES: "@trade",
}


class BinanceWebSocket(BaseExchangeWebSocket):
    def __init__(
        self,
        adapter: BaseExchangeAdapter,
        config: WebSocketConfig | None = None,
        testnet: bool = True,
    ) -> None:
        super().__init__(exchange_id="binance", adapter=adapter, config=config)
        self.endpoint = BINANCE_WS_TESTNET if testnet else BINANCE_WS_MAINNET
        self._ws: Any = None
        self._subscriptions: list[str] = []

    async def connect(self) -> None:
        try:
            import websockets
        except ImportError as exc:
            raise RuntimeError("websockets library is required for BinanceWebSocket. Install it with: pip install websockets") from exc

        self._ws = await websockets.connect(self.endpoint, ping_interval=self.config.ping_interval)
        logger.info("Binance WebSocket connected", endpoint=self.endpoint)

    async def disconnect(self) -> None:
        if self._ws:
            await self._ws.close()
            self._ws = None
            logger.info("Binance WebSocket disconnected")

    async def subscribe(self, channel: str, symbol: str, **kwargs: Any) -> None:
        stream_name = self._build_stream_name(channel, symbol, **kwargs)
        payload = {"method": "SUBSCRIBE", "params": [stream_name], "id": len(self._subscriptions) + 1}
        await self._send(payload)
        self._subscriptions.append(stream_name)
        logger.debug("Subscribed", stream=stream_name)

    async def unsubscribe(self, channel: str, symbol: str, **kwargs: Any) -> None:
        stream_name = self._build_stream_name(channel, symbol, **kwargs)
        payload = {"method": "UNSUBSCRIBE", "params": [stream_name], "id": len(self._subscriptions) + 1}
        await self._send(payload)
        if stream_name in self._subscriptions:
            self._subscriptions.remove(stream_name)
        logger.debug("Unsubscribed", stream=stream_name)

    async def _send(self, payload: dict[str, Any]) -> None:
        if self._ws:
            await self._ws.send(json.dumps(payload))

    async def _listen(self) -> None:
        if not self._ws:
            return
        async for message in self._ws:
            data = json.loads(message)
            if "result" in data and data["result"] is None:
                continue
            if "e" in data:
                await self._handle_message(data)

    async def _handle_message(self, data: dict[str, Any]) -> None:
        event_type = data.get("e", "")
        symbol = data.get("s", "")
        stream_channel = self._parse_channel(event_type)
        if not stream_channel:
            logger.debug("Unhandled message type", event_type=event_type)
            return

        message = StreamMessage(
            exchange_id=self.exchange_id,
            channel=stream_channel,
            symbol=self._normalize_symbol(symbol),
            data=data,
        )
        await self._emit(message)

    def _build_stream_name(self, channel: str, symbol: str, **kwargs: Any) -> str:
        normalized_symbol = self._normalize_symbol(symbol).lower()
        if channel == StreamChannel.CANDLES:
            interval = kwargs.get("interval", "1m")
            return f"{normalized_symbol}@kline_{interval}"
        if channel == StreamChannel.ORDER_BOOK:
            levels = kwargs.get("levels", "20")
            return f"{normalized_symbol}@depth{levels}"
        suffix = _CHANNEL_MAP.get(StreamChannel(channel), channel)
        return f"{normalized_symbol}{suffix}"

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        return symbol.upper().replace("/", "").replace("-", "").replace("_", "")

    @staticmethod
    def _parse_channel(event_type: str) -> str | None:
        mapping = {
            "24hrTicker": StreamChannel.TICKER,
            "kline": StreamChannel.CANDLES,
            "depth": StreamChannel.ORDER_BOOK,
            "trade": StreamChannel.TRADES,
        }
        return mapping.get(event_type)

    async def _resubscribe(self) -> None:
        for stream_name in list(self._subscriptions):
            payload = {"method": "SUBSCRIBE", "params": [stream_name], "id": len(self._subscriptions) + 1}
            await self._send(payload)
            logger.debug("Resubscribed after reconnect", stream=stream_name)
