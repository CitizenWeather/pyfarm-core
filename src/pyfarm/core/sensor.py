"""The sensor contract the control engine depends on.

Real hardware drivers and simulated/replay sensors implement the same
interface, so one runner can drive a live tent or a recording. Drivers live in
``pyfarm-control`` (and, in a later phase, ``pyfarm-iot``); this is the contract
they implement.
"""

from __future__ import annotations

import abc

from pyfarm.core.models import SensorReading


class Sensor(abc.ABC):
    """A source of readings for a single metric (e.g. ``temperature``)."""

    def __init__(self, metric: str, unit: str = "") -> None:
        self.metric = metric
        self.unit = unit

    @abc.abstractmethod
    async def read(self) -> SensorReading:
        """Return the current reading, or raise
        :class:`pyfarm.core.errors.SensorReadError`."""
        raise NotImplementedError
