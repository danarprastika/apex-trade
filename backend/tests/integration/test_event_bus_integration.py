import pytest


@pytest.fixture
def integration_event_bus():
    from app.events.bus import EventBus
    return EventBus()


def test_event_bus_publish_and_consume(integration_event_bus):
    events_received = []

    async def handler(event):
        events_received.append(event)

    integration_event_bus.subscribe("TEST.EVENT", handler)

    async def run_publish():
        from app.events.types import ApexEvent
        event = ApexEvent(type="TEST.EVENT", payload={"data": "test"})
        await integration_event_bus.publish(event)

    import asyncio
    asyncio.get_event_loop().run_until_complete(run_publish())

    assert len(events_received) == 1
    assert events_received[0].payload["data"] == "test"


def test_event_bus_multiple_subscribers(integration_event_bus):
    events_received = []

    async def handler1(event):
        events_received.append(("h1", event))

    async def handler2(event):
        events_received.append(("h2", event))

    integration_event_bus.subscribe("MULTI.EVENT", handler1)
    integration_event_bus.subscribe("MULTI.EVENT", handler2)

    async def run_publish():
        from app.events.types import ApexEvent
        event = ApexEvent(type="MULTI.EVENT", payload={"multi": True})
        await integration_event_bus.publish(event)

    import asyncio
    asyncio.get_event_loop().run_until_complete(run_publish())

    assert len(events_received) == 2
