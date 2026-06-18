import pytest

from app.events.bus import EventBus
from app.events.dlq import DeadLetterQueue
from app.events.handler import EventHandler
from app.events.types import ApexEvent


class TestEventBus:
    @pytest.fixture
    def bus(self) -> EventBus:
        return EventBus()

    @pytest.mark.asyncio
    async def test_publish_no_handlers(self, bus: EventBus) -> None:
        event = ApexEvent(type="TEST.EVENT", payload={"data": 1})
        await bus.publish(event)

    @pytest.mark.asyncio
    async def test_publish_single_handler(self, bus: EventBus) -> None:
        results = []

        async def handler(event: ApexEvent) -> None:
            results.append(event)

        bus.subscribe("TEST.EVENT", handler)
        event = ApexEvent(type="TEST.EVENT", payload={"data": "test"})
        await bus.publish(event)
        assert len(results) == 1
        assert results[0].payload["data"] == "test"

    @pytest.mark.asyncio
    async def test_publish_multiple_handlers(self, bus: EventBus) -> None:
        results = []

        async def handler1(event: ApexEvent) -> None:
            results.append(("h1", event))

        async def handler2(event: ApexEvent) -> None:
            results.append(("h2", event))

        bus.subscribe("TEST.EVENT", handler1)
        bus.subscribe("TEST.EVENT", handler2)
        event = ApexEvent(type="TEST.EVENT", payload={})
        await bus.publish(event)
        assert len(results) == 2


class TestDeadLetterQueue:
    @pytest.fixture
    def dlq(self) -> DeadLetterQueue:
        return DeadLetterQueue()

    def test_push_and_get(self, dlq: DeadLetterQueue) -> None:
        event = ApexEvent(type="TEST", payload={"x": 1})
        dlq.push(event, "test error", "test_handler")
        failed = dlq.get_failed()
        assert len(failed) == 1
        assert failed[0]["error"] == "test error"

    def test_clear(self, dlq: DeadLetterQueue) -> None:
        event = ApexEvent(type="TEST", payload={"x": 1})
        dlq.push(event, "error", "handler")
        dlq.clear()
        assert len(dlq.get_failed()) == 0


class ConcreteHandler(EventHandler):
    async def process(self, event: ApexEvent) -> None:
        if event.payload.get("fail"):
            raise ValueError("Intentional failure")


class TestEventHandler:
    @pytest.mark.asyncio
    async def test_handle_success(self) -> None:
        handler = ConcreteHandler("test")
        event = ApexEvent(type="TEST", payload={})
        result = await handler.handle(event)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_failure(self) -> None:
        handler = ConcreteHandler("test", max_retries=1)
        event = ApexEvent(type="TEST", payload={"fail": True})
        result = await handler.handle(event)
        assert result is False

    @pytest.mark.asyncio
    async def test_handle_duplicate(self) -> None:
        handler = ConcreteHandler("test")
        event = ApexEvent(type="TEST", payload={}, id="same-id")
        await handler.handle(event)
        await handler.handle(event)
        assert len(handler._processed_events) == 1
