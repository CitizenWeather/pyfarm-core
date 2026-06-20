"""Core data models shared across pyfarm."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class EventType(str, Enum):
    """Event type enumeration."""
    SENSOR_READING = "sensor_reading"
    ACTUATOR_COMMAND = "actuator_command"
    ALERT = "alert"
    STAGE_TRANSITION = "stage_transition"
    HEALTH_CHECK = "health_check"


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
    actuator_id: str
    command: str
    value: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    error: Optional[str] = None


@dataclass
class ControlEvent:
    """An event in the control loop lifecycle."""
    event_type: EventType
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    grow_id: str = ""
    stage_name: str = ""
    metric: str = ""
    value: Any = None
    message: str = ""
    severity: str = "info"  # info, warning, alert, critical

    def __post_init__(self):
        if isinstance(self.event_type, str):
            self.event_type = EventType(self.event_type)
