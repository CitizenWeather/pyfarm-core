"""Sensor abstraction."""

from __future__ import annotations

import abc

from pyfarm.control.engine.context import SensorReading


class Sensor(abc.ABC):
    def __init__(self, metric: str, unit: str = "") -> None:
        self.metric = metric
        self.unit = unit

    @abc.abstractmethod
    async def read(self) -> SensorReading:
        raise NotImplementedError
