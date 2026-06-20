"""Canonical domain models shared across PyFarm.

These are the single source of truth for the value types the control engine
reads and writes. ``pyfarm-control`` (and any other consumer such as a future
``pyfarm-iot`` driver package) imports them from here rather than redefining
them, so a ``SensorReading`` produced by a driver is the same type the engine,
the persistence layer and the status API all speak.

The dataclass shapes match what the control engine has always used at runtime
(``SensorReading.flatline_minutes()``, ``ActuatorState.seconds_in_state()``,
free-form string ``ControlEvent.kind``); the ``EventKind`` and ``Unit`` enums
are provided as well-known constants for producers that want them.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


def _now() -> datetime:
    return datetime.now(timezone.utc)


class EventKind(str, Enum):
    """Well-known :attr:`ControlEvent.kind` values.

    ``kind`` is a plain string so callers may use ad-hoc kinds, but these are
    the ones the engine emits and downstream sinks may want to switch on.
    """

    SYSTEM = "system"
    STAGE_ADVANCED = "stage_advanced"
    ACTUATOR = "actuator"
    ALERT = "alert"
    SENSOR_FAILURE = "sensor_failure"


class Unit(str, Enum):
    """Well-known sensor units."""

    CELSIUS = "celsius"
    PERCENT = "percent"
    PPM = "ppm"
    UNITLESS = "unitless"


@dataclass
class SensorReading:
    """A single sensor sample."""

    value: float
    unit: str
    timestamp: datetime = field(default_factory=_now)

    def flatline_minutes(
        self, *, value_changed_at: datetime, now: datetime | None = None
    ) -> float:
        now = now or _now()
        return max(0.0, (now - value_changed_at).total_seconds() / 60.0)


@dataclass
class ActuatorState:
    """What the engine last commanded an actuator to do."""

    name: str
    on: bool = False
    command: Any = False
    last_changed: datetime = field(default_factory=_now)

    def seconds_in_state(self, now: datetime | None = None) -> float:
        now = now or _now()
        return max(0.0, (now - self.last_changed).total_seconds())


@dataclass
class ControlEvent:
    """A timestamped record of something the engine did or noticed."""

    kind: str  # "stage_advanced", "actuator", "alert", "sensor_failure", ...
    message: str
    timestamp: datetime = field(default_factory=_now)
    data: dict[str, Any] = field(default_factory=dict)
