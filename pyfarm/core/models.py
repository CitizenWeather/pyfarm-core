from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any


class Unit(str, Enum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"
    PERCENT = "percent"
    PPM = "ppm"
    LUX = "lux"
    KPA = "kpa"
    UNITLESS = "unitless"


@dataclass
class SensorReading:
    value: float
    unit: Unit
    timestamp: datetime
    metric: str = ""
    stale: bool = False


@dataclass
class ActuatorState:
    name: str
    on: bool
    last_changed: datetime
    command_value: float | None = None


class EventKind(str, Enum):
    SENSOR_READ = "sensor_read"
    ACTUATOR_COMMAND = "actuator_command"
    STAGE_TRANSITION = "stage_transition"
    ALERT_FIRED = "alert_fired"
    SENSOR_FAILURE = "sensor_failure"
    SYSTEM = "system"


@dataclass
class ControlEvent:
    kind: EventKind
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: dict[str, Any] = field(default_factory=dict)
