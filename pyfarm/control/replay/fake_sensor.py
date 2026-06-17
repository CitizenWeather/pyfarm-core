"""A sensor that replays a recorded series of readings."""

from __future__ import annotations

import csv
from collections.abc import Iterable
from datetime import datetime, timedelta, timezone
from pathlib import Path

from pyfarm.control.sensors.base import Sensor, SensorReadError, SensorReading

# Synthetic timestamps start here when a dataset has no timestamp column, so
# that replays are fully deterministic and not tied to wall-clock time.
_SYNTHETIC_EPOCH = datetime(2000, 1, 1, tzinfo=timezone.utc)


class ReplayExhausted(SensorReadError):
    """Raised by :meth:`ReplaySensor.read` when the recording runs out.

    A subclass of :class:`SensorReadError` so a runner that already handles
    sensor failures treats the end of a recording as just another read failure.
    """


class ReplaySensor(Sensor):
    """Replays a fixed sequence of :class:`SensorReading` for one metric.

    Each :meth:`read` returns the next reading in the recording. When the
    recording is exhausted, ``read`` either raises :class:`ReplayExhausted`
    (default) or wraps back to the start if ``loop`` is set.
    """

    def __init__(
        self,
        metric: str,
        unit: str,
        readings: Iterable[SensorReading | float | tuple[datetime, float]],
        *,
        loop: bool = False,
    ) -> None:
        self.metric = metric
        self.unit = unit
        self.loop = loop
        self._readings = self._coerce_readings(readings)
        self._index = 0

    def _coerce_readings(
        self, readings: Iterable[SensorReading | float | tuple[datetime, float]]
    ) -> list[SensorReading]:
        coerced: list[SensorReading] = []
        for position, item in enumerate(readings):
            if isinstance(item, SensorReading):
                coerced.append(item)
            elif isinstance(item, tuple):
                timestamp, value = item
                coerced.append(
                    SensorReading(self.metric, float(value), self.unit, timestamp)
                )
            else:
                coerced.append(
                    SensorReading(
                        self.metric,
                        float(item),
                        self.unit,
                        self._synthetic_timestamp(position),
                    )
                )
        return coerced

    @staticmethod
    def _synthetic_timestamp(position: int) -> datetime:
        return _SYNTHETIC_EPOCH + timedelta(seconds=position)

    @classmethod
    def from_csv(
        cls,
        path: str | Path,
        metric: str,
        unit: str,
        *,
        value_column: str | None = None,
        timestamp_column: str | None = "timestamp",
        loop: bool = False,
    ) -> "ReplaySensor":
        """Build a :class:`ReplaySensor` from a CSV recording.

        ``value_column`` defaults to ``metric``. If ``timestamp_column`` is
        present in the file its values are parsed as ISO-8601; otherwise
        synthetic, deterministic timestamps are generated one second apart.
        """
        path = Path(path)
        value_column = value_column or metric
        try:
            text = path.read_text()
        except OSError as exc:
            raise SensorReadError(
                f"Could not read replay file {path}: {exc}"
            ) from exc

        reader = csv.DictReader(text.splitlines())
        if reader.fieldnames is None or value_column not in reader.fieldnames:
            raise SensorReadError(
                f"Replay file {path} has no column {value_column!r} "
                f"(columns: {reader.fieldnames})"
            )
        has_timestamp = (
            timestamp_column is not None and timestamp_column in reader.fieldnames
        )

        readings: list[SensorReading] = []
        for position, row in enumerate(reader):
            raw_value = row[value_column]
            if raw_value is None or raw_value.strip() == "":
                continue
            try:
                value = float(raw_value)
            except ValueError as exc:
                raise SensorReadError(
                    f"Replay file {path}: row {position} has non-numeric "
                    f"{value_column}={raw_value!r}"
                ) from exc
            if has_timestamp:
                timestamp = _parse_timestamp(
                    row[timestamp_column], path, position  # type: ignore[index]
                )
            else:
                timestamp = cls._synthetic_timestamp(position)
            readings.append(SensorReading(metric, value, unit, timestamp))

        if not readings:
            raise SensorReadError(f"Replay file {path} contained no readings")
        return cls(metric, unit, readings, loop=loop)

    @property
    def remaining(self) -> int:
        """How many readings are left before the recording is exhausted."""
        if self.loop:
            return len(self._readings)
        return max(0, len(self._readings) - self._index)

    async def read(self) -> SensorReading:
        if self._index >= len(self._readings):
            if not self.loop:
                raise ReplayExhausted(
                    f"Replay for metric {self.metric!r} exhausted after "
                    f"{len(self._readings)} readings"
                )
            self._index = 0
        reading = self._readings[self._index]
        self._index += 1
        return reading


def _parse_timestamp(raw: str, path: Path, position: int) -> datetime:
    try:
        return datetime.fromisoformat(raw.strip())
    except ValueError as exc:
        raise SensorReadError(
            f"Replay file {path}: row {position} has unparseable timestamp "
            f"{raw!r} (expected ISO-8601)"
        ) from exc
