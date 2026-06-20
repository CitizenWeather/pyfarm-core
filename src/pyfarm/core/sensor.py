"""Sensor protocol for pyfarm."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Optional

from pyfarm.core.models import SensorReading


class Sensor(ABC):
    """Base class for all sensors."""

    def __init__(self, sensor_id: str, metric: str, unit: str):
        self.sensor_id = sensor_id
        self.metric = metric
        self.unit = unit
        self.last_reading: Optional[SensorReading] = None

    @abstractmethod
    async def read(self) -> SensorReading:
        """Read from this sensor. Return a SensorReading."""
        pass

    @abstractmethod
    async def check_health(self) -> bool:
        """Check if sensor is healthy. Return True if healthy."""
        pass

    @property
    def exhausted(self) -> bool:
        """
        Whether the sensor has no more data (e.g., replay sensor at end of CSV).
        Default: False. Override in replay/file-backed sensors.
        """
        return False
