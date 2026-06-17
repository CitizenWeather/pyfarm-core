"""The sensor interface the control engine depends on."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


class SensorReadError(Exception):
    """Raised by a :class:`Sensor` when it cannot produce a reading.

    The runner is expected to catch this and degrade gracefully (use the last
    known value, raise an alert) rather than crash the whole grow.
    """


@dataclass(frozen=True)
class SensorReading:
    """A single measurement from a sensor.

    ``metric`` is the namespaced quantity (``"temperature"``, ``"humidity_rh"``,
    ``"co2_ppm"``) that controllers and expressions address. ``value`` is in the
    units named by ``unit``; ``timestamp`` is when the measurement was taken.
    """

    metric: str
    value: float
    unit: str
    timestamp: datetime


class Sensor(ABC):
    """A source of readings for one metric.

    Implementations expose the metric they report via :attr:`metric` and yield a
    :class:`SensorReading` from :meth:`read`. ``read`` is async so a single tick
    can poll several sensors (I2C, UART, MQTT, a replay file) without blocking.
    """

    metric: str

    @abstractmethod
    async def read(self) -> SensorReading:
        """Return the current reading, or raise :class:`SensorReadError`."""
        raise NotImplementedError
