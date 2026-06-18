"""Domain-agnostic spec primitives. All domain specs (GrowSpec, BioSpec, etc.) extend BaseSpec."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class DurationSpec(BaseModel):
    """Stage duration bounds."""
    min_days: int = 0
    max_days: int


class ExitConditionSpec(BaseModel):
    metric: str
    threshold: str


class BaseStage(BaseModel):
    """Fields the engine needs from any stage, regardless of domain."""
    name: str
    duration: DurationSpec
    exit_condition: ExitConditionSpec
    controls_disabled: list[str] = Field(default_factory=list)


class AlertRule(BaseModel):
    condition: str
    severity: str
    message: str
    channels: list[str] = Field(default_factory=list)
    cooldown_minutes: int = 0


class ActuatorSafety(BaseModel):
    max_on_seconds: int | None = None
    min_off_seconds: int | None = None
    max_on_minutes: int | None = None


class BaseActuatorSpec(BaseModel):
    kind: str
    interlock: str | None = None
    safety: ActuatorSafety = Field(default_factory=ActuatorSafety)


class BaseSpecMetadata(BaseModel):
    name: str
    author: str | None = None
    description: str | None = None


class BaseSpec(BaseModel):
    """Generic spec. Domain specs extend this with domain-specific fields."""
    spec_version: str
    kind: str
    metadata: BaseSpecMetadata
    stages: list[BaseStage]
    alerts: list[AlertRule] = Field(default_factory=list)
    actuators: dict[str, BaseActuatorSpec] = Field(default_factory=dict)
    notifications: Any = None
