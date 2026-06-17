from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class EventKind(str, Enum):
    SYSTEM = "system"
    STAGE_TRANSITION = "stage_transition"
    SENSOR_FAILURE = "sensor_failure"
    ALERT_FIRED = "alert_fired"


class Unit(str, Enum):
    CELSIUS = "celsius"
    PERCENT = "percent"
    PPM = "ppm"
    UNITLESS = "unitless"


@dataclass
class SensorReading:
    value: float
    unit: Unit
    timestamp: datetime
    metric: str

    @property
    def stale(self) -> bool:
        ts = self.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        age = datetime.now(timezone.utc) - ts
        return age.total_seconds() > 30


@dataclass
class ControlEvent:
    kind: EventKind
    message: str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ActuatorState:
    name: str
    state: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_toggled_at: datetime | None = None
