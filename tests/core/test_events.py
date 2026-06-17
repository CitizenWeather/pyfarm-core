import asyncio

from pyfarm.core.events import EventBus
from pyfarm.core.models import ControlEvent, EventKind


def _event(message: str) -> ControlEvent:
    return ControlEvent(kind=EventKind.SYSTEM, message=message)


class RecordingSink:
    def __init__(self) -> None:
        self.seen: list[str] = []

    async def handle(self, event: ControlEvent) -> None:
        self.seen.append(event.message)


class ExplodingSink:
    async def handle(self, event: ControlEvent) -> None:
        raise RuntimeError("boom")


def test_sink_receives_events_in_order():
    bus = EventBus()
    sink = RecordingSink()
    bus.subscribe(sink)
    for msg in ("a", "b", "c"):
        bus.emit(_event(msg))
    asyncio.run(bus.drain())
    assert sink.seen == ["a", "b", "c"]


def test_drain_clears_buffer():
    bus = EventBus()
    sink = RecordingSink()
    bus.subscribe(sink)
    bus.emit(_event("once"))
    asyncio.run(bus.drain())
    asyncio.run(bus.drain())  # second drain delivers nothing
    assert sink.seen == ["once"]


def test_failing_sink_does_not_block_others():
    bus = EventBus()
    good = RecordingSink()
    bus.subscribe(ExplodingSink())
    bus.subscribe(good)
    bus.emit(_event("x"))
    asyncio.run(bus.drain())  # must not raise
    assert good.seen == ["x"]


def test_overflow_drops_oldest_without_raising():
    bus = EventBus(maxlen=2)
    sink = RecordingSink()
    bus.subscribe(sink)
    bus.emit(_event("1"))
    bus.emit(_event("2"))
    bus.emit(_event("3"))  # evicts "1"
    asyncio.run(bus.drain())
    assert sink.seen == ["2", "3"]


def test_drain_with_no_sinks_clears_buffer():
    bus = EventBus()
    bus.emit(_event("orphan"))
    asyncio.run(bus.drain())
    # nothing subscribed yet; buffer must not retain the event indefinitely
    sink = RecordingSink()
    bus.subscribe(sink)
    asyncio.run(bus.drain())
    assert sink.seen == []
