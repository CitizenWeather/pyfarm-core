"""Pydantic models for the GrowSpec YAML format."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pyfarm.control.spec.base import (
    ActuatorSafety,
    BaseActuatorSpec,
    BaseSpec,
    BaseSpecMetadata,
    BaseStage,
    DurationSpec,
    ExitConditionSpec,
)

# Re-export for backward compatibility
__all__ = [
    "ActuatorSafety", "ActuatorSpec", "AlertRule", "Duration",
    "ExitCondition", "GrowSpec", "LightSetpoint", "Metadata",
    "NotificationsConfig", "RatioSetpoint", "Setpoints", "Stage",
    "StrictModel", "TemperatureSetpoint", "ToleranceSetpoint", "VPDConstraint",
]

_SCHEDULE_RE = re.compile(r"^(\d{1,2})/(\d{1,2})$")


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


# Aliases kept for existing callers
Duration = DurationSpec
ExitCondition = ExitConditionSpec


class Metadata(BaseSpecMetadata):
    model_config = ConfigDict(extra="forbid")
    name: str
    species: str
    substrate: str
    author: str
    registry: str


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


class Stage(BaseStage):
    model_config = ConfigDict(extra="forbid")
    setpoints: Setpoints
    controls_disabled: list[str] = []
    vpd: VPDConstraint | None = None


class AlertRule(StrictModel):
    condition: str
    severity: Literal["critical", "warning", "info"]
    message: str
    channels: list[str]
    cooldown_minutes: int = 0


class ActuatorSpec(BaseActuatorSpec):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["relay", "pwm", "mqtt"]
    gpio: int | None = Field(default=None, ge=0, le=27)
    pwm: bool = False
    interlock: str | None = None
    safety: ActuatorSafety = Field(default_factory=ActuatorSafety)


class NotificationsConfig(StrictModel):
    channels: dict[str, dict] = {}


class GrowSpec(BaseSpec):
    model_config = ConfigDict(extra="forbid")
    spec_version: Literal["1.0"]
    kind: Literal["GrowSpec"]
    metadata: Metadata
    stages: list[Stage]
    alerts: list[AlertRule] = []
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
