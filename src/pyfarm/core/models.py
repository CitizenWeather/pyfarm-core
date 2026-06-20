"""Core data models shared across pyfarm."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class EventType(str, Enum):
    """Event type enumeration (control event categorization)."""
    SENSOR_READING = "sensor_reading"
    ACTUATOR_COMMAND = "actuator_command"
    ALERT = "alert"
    STAGE_TRANSITION = "stage_transition"
    HEALTH_CHECK = "health_check"


class EventKind(str, Enum):
    """Event kind enumeration (operational event types)."""
    SYSTEM = "system"
    ALERT_FIRED = "alert_fired"
    SENSOR_FAILURE = "sensor_failure"
    STAGE_TRANSITION = "stage_transition"


class Unit(str, Enum):
    """Measurement unit enumeration."""
    CELSIUS = "°C"
    FAHRENHEIT = "°F"
    PERCENT = "%"
    PPM = "ppm"
    EC = "mS/cm"
    PH = "pH"
    LUX = "lux"
    PPFD = "μmol/m²/s"
    UNITLESS = ""


@dataclass
class SensorReading:
    """A single sensor measurement."""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metric: str = ""
    value: float = 0.0
    unit: str = ""
    sensor_id: str = ""
    error: Optional[str] = None

    def __post_init__(self):
        if not self.metric:
            raise ValueError("metric is required")


@dataclass
class ActuatorState:
    """State of an actuator."""
    name: str
    state: bool
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_toggled_at: Optional[datetime] = None


@dataclass
class ControlEvent:
    """An event in the control loop lifecycle."""
    kind: EventKind
    message: str = ""
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    data: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.kind, str):
            self.kind = EventKind(self.kind)
