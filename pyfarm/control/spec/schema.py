"""Pydantic models for the GrowSpec YAML format."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator


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


class LightSetpoint(StrictModel):
    schedule: str
    intensity_lux: float | None = None


class Setpoints(StrictModel):
    temperature: TemperatureSetpoint
    humidity_rh: ToleranceSetpoint
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
    gpio: int | None = None
    pwm: bool = False
    interlock: str | None = None
    safety: ActuatorSafety = ActuatorSafety()


class NotificationsConfig(StrictModel):
    channels: dict[str, dict[str, str]] = {}


class GrowSpec(StrictModel):
    spec_version: str
    kind: Literal["GrowSpec"]
    metadata: Metadata
    stages: list[Stage]
    alerts: list[AlertRule] = []
    actuators: dict[str, ActuatorSpec] = {}
    notifications: NotificationsConfig | None = None
