"""Pydantic models for the GrowSpec YAML format."""

from __future__ import annotations

import re
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

_SCHEDULE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Metadata(StrictModel):
    name: str
    species: str
    substrate: str
    author: str
    registry: str


class Duration(StrictModel):
    min_days: int
    max_days: int

    @model_validator(mode="after")
    def _check_range(self) -> "Duration":
        if self.max_days < self.min_days:
            raise ValueError(
                f"max_days ({self.max_days}) must be >= min_days "
                f"({self.min_days})"
            )
        return self


class ExitCondition(StrictModel):
    metric: str
    threshold: str


class ToleranceSetpoint(StrictModel):
    target: float
    tolerance: float = 0.0

    @model_validator(mode="after")
    def _check_tolerance(self) -> "ToleranceSetpoint":
        if self.tolerance < 0:
            raise ValueError("tolerance must be >= 0")
        return self


class TemperatureSetpoint(ToleranceSetpoint):
    unit: Literal["celsius", "fahrenheit"]


class RatioSetpoint(ToleranceSetpoint):
    """A setpoint expressed as a 0-1 ratio, e.g. relative humidity."""

    @model_validator(mode="after")
    def _check_ratio(self) -> "RatioSetpoint":
        if not 0 <= self.target <= 1:
            raise ValueError(
                f"target {self.target} must be between 0 and 1 "
                "(this is a ratio, e.g. 0.90 for 90%)"
            )
        return self


class LightSetpoint(StrictModel):
    schedule: str
    intensity_lux: float | None = None

    @model_validator(mode="after")
    def _check_schedule(self) -> "LightSetpoint":
        match = _SCHEDULE_RE.match(self.schedule)
        if not match:
            raise ValueError(
                f"schedule {self.schedule!r} must look like "
                "'<hours_on>/<hours_off>', e.g. '12/12'"
            )
        hours_on, hours_off = int(match.group(1)), int(match.group(2))
        if hours_on > 24 or hours_off > 24 or hours_on + hours_off != 24:
            raise ValueError(
                f"schedule {self.schedule!r} must be two values that sum to "
                f"24 hours (got {hours_on}+{hours_off})"
            )
        return self


class Setpoints(StrictModel):
    temperature: TemperatureSetpoint
    humidity_rh: RatioSetpoint
    co2_ppm: ToleranceSetpoint
    light: LightSetpoint


class VPDConstraint(StrictModel):
    target: float
    tolerance: float = 0.0


class Stage(StrictModel):
    name: str
    duration: Duration
    exit_condition: ExitCondition
    setpoints: Setpoints
    controls_disabled: list[str] = []
    vpd: VPDConstraint | None = None


class AlertRule(StrictModel):
    condition: str
    severity: Literal["critical", "warning", "info"]
    message: str
    channels: list[str]
    cooldown_minutes: int = 0


class ActuatorSafety(StrictModel):
    max_on_seconds: int | None = None
    min_off_seconds: int | None = None
    max_on_minutes: int | None = None


class ActuatorSpec(StrictModel):
    kind: Literal["relay", "pwm", "mqtt"]
    gpio: int | None = Field(default=None, ge=0, le=27)
    pwm: bool = False
    interlock: str | None = None
    safety: ActuatorSafety = ActuatorSafety()


SensorKind = Literal["dht22_temp", "dht22_humidity", "analog", "fake", "replay"]


class SensorSpec(StrictModel):
    """Declares one sensor the engine should construct and poll.

    ``metric`` is the namespaced quantity the reading is recorded under
    (``temperature``, ``humidity_rh``, ``co2_ppm``, ...). The remaining fields
    are kind-specific:

    * ``dht22_temp`` / ``dht22_humidity`` — require ``gpio``.
    * ``analog`` — requires ``gpio`` (ADC channel); ``scale``/``offset`` convert
      the raw 0–1 reading to engineering units.
    * ``fake`` — requires ``value`` (a constant, for demos/bring-up).
    * ``replay`` — requires ``csv``; ``column`` defaults to ``metric``.
    """

    kind: SensorKind
    metric: str
    unit: str = ""
    gpio: int | None = Field(default=None, ge=0, le=27)
    value: float | None = None
    scale: float = 1.0
    offset: float = 0.0
    csv: str | None = None
    column: str | None = None


class NotificationsConfig(StrictModel):
    channels: dict[str, dict[str, Any]] = {}


class GrowSpec(StrictModel):
    spec_version: Literal["1.0"]
    kind: Literal["GrowSpec"]
    metadata: Metadata
    stages: list[Stage]
    alerts: list[AlertRule] = []
    sensors: dict[str, SensorSpec] = {}
    actuators: dict[str, ActuatorSpec] = {}
    notifications: NotificationsConfig | None = None

    @model_validator(mode="after")
    def _check_stages(self) -> "GrowSpec":
        if not self.stages:
            raise ValueError("stages must not be empty")
        names = [stage.name for stage in self.stages]
        if len(names) != len(set(names)):
            raise ValueError(f"stage names must be unique, got {names}")
        return self
