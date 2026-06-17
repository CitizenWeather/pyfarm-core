from __future__ import annotations

import sys
from collections import deque
from typing import Protocol, runtime_checkable

from pyfarm.core.models import ControlEvent


@runtime_checkable
class EventSink(Protocol):
    """A consumer of control events. Sinks are notified asynchronously on drain."""

    async def handle(self, event: ControlEvent) -> None: ...


class EventBus:
    """
    Sync-emit / async-fan-out event spine.

    Producers call `emit(event)` synchronously (it only appends to a bounded
    buffer, so it is safe to call from anywhere, including non-async code).
    The owner periodically calls `await drain()`, which delivers every buffered
    event to every subscribed sink. Each sink delivery is isolated: a sink that
    raises cannot stop other sinks or drop the tick — the error is reported and
    delivery continues.
    """

    def __init__(self, maxlen: int = 1000):
        self._sinks: list[EventSink] = []
        self._pending: deque[ControlEvent] = deque(maxlen=maxlen)

    def subscribe(self, sink: EventSink) -> None:
        self._sinks.append(sink)

    def emit(self, event: ControlEvent) -> None:
        """Buffer an event for delivery. Never blocks; oldest is dropped on overflow."""
        if len(self._pending) == self._pending.maxlen:
            dropped = self._pending[0]
            print(
                f"EventBus buffer full — dropping oldest event ({dropped.kind})",
                file=sys.stderr,
            )
        self._pending.append(event)

    async def drain(self) -> None:
        """Deliver all buffered events to all sinks, in FIFO order, isolating failures."""
        if not self._sinks:
            self._pending.clear()
            return
        while self._pending:
            event = self._pending.popleft()
            for sink in self._sinks:
                try:
                    await sink.handle(event)
                except Exception as e:  # noqa: BLE001 — one bad sink must not kill the loop
                    print(
                        f"EventSink {type(sink).__name__} failed on {event.kind}: {e}",
                        file=sys.stderr,
                    )
