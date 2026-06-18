"""Replay sensors: drive the full control loop from recorded data."""

from __future__ import annotations

import csv
from collections.abc import Iterable, Sequence
from pathlib import Path

from pyfarm.control.engine.context import SensorReading
from pyfarm.control.engine.errors import ReplayExhausted
from pyfarm.control.sensors.base import Sensor


class ReplaySensor(Sensor):
    def __init__(
        self,
        metric: str,
        values: Sequence[float],
        unit: str = "",
        *,
        loop: bool = False,
    ) -> None:
        super().__init__(metric, unit)
        self._values = list(values)
        self._loop = loop
        self._index = 0

    @property
    def exhausted(self) -> bool:
        return not self._loop and self._index >= len(self._values)

    async def read(self) -> SensorReading:
        if not self._values:
            raise ReplayExhausted(f"replay sensor {self.metric!r} has no data")
        if self._index >= len(self._values):
            if not self._loop:
                raise ReplayExhausted(
                    f"replay sensor {self.metric!r} exhausted after "
                    f"{len(self._values)} samples"
                )
            self._index = 0
        value = self._values[self._index]
        self._index += 1
        return SensorReading(value=value, unit=self.unit)


def replay_sensors_from_rows(
    rows: Iterable[dict[str, str]],
    units: dict[str, str] | None = None,
) -> list[ReplaySensor]:
    units = units or {}
    series: dict[str, list[float]] = {}
    ignored = {"timestamp", "time", "ts", "datetime"}
    for row in rows:
        for key, raw in row.items():
            if key is None or key.lower() in ignored or raw in (None, ""):
                continue
            series.setdefault(key, []).append(float(raw))
    return [
        ReplaySensor(metric, values, unit=units.get(metric, ""))
        for metric, values in series.items()
    ]


def replay_sensors_from_csv(
    path: str | Path,
    units: dict[str, str] | None = None,
) -> list[ReplaySensor]:
    with Path(path).open(newline="") as handle:
        return replay_sensors_from_rows(csv.DictReader(handle), units=units)
