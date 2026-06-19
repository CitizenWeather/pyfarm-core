"""Cross-field validation for a loaded :class:`GrowSpec`.

Pydantic handles structural/type validation. This module checks things that
span multiple fields: VPD consistency between temperature/humidity setpoints,
exit-condition thresholds, and the safety of alert/interlock expressions.
"""

from __future__ import annotations

import math
import re

from pyfarm.control.exceptions import SpecValidationError
from pyfarm.control.expr.evaluator import SafeExpressionEvaluator
from pyfarm.control.spec.schema import GrowSpec, Stage, TemperatureSetpoint

_COMPARISON_THRESHOLD_RE = re.compile(r"^(>=|<=|==|!=|>|<)\s*-?\d+(\.\d+)?$")
_COMPARISON_PREFIXES = (">=", "<=", "==", "!=", ">", "<")

_KNOWN_CONTROL_NAMES = {"misting", "FAE", "exhaust_fan", "heater", "light"}

# Namespace available to alert/interlock expressions.
_BASE_NAMESPACE = {
    "temperature.current",
    "humidity_rh.current",
    "co2_ppm.current",
    "vpd.current",
    "stage",
    "target",
    "tolerance",
    "sensor.*",
}


def validate_spec(spec: GrowSpec) -> None:
    """Run cross-field validation on ``spec``, raising
    :class:`SpecValidationError` on the first problem found."""
    evaluator = SafeExpressionEvaluator()
    namespace = _build_namespace(spec)

    for stage in spec.stages:
        _check_vpd_consistency(stage)
        _check_exit_condition_threshold(stage)
        _check_controls_disabled(stage, spec)

    for alert in spec.alerts:
        evaluator.validate(alert.condition, namespace)

    for name, actuator in spec.actuators.items():
        if actuator.interlock is not None:
            try:
                evaluator.validate(actuator.interlock, namespace)
            except SpecValidationError as exc:
                raise SpecValidationError(
                    f"Actuator {name!r}: {exc}"
                ) from exc

    for name, sensor in spec.sensors.items():
        _check_sensor(name, sensor)


def _check_sensor(name: str, sensor) -> None:
    """Validate that a sensor declaration has the fields its kind requires."""
    kind = sensor.kind
    if kind in ("dht22_temp", "dht22_humidity", "analog") and sensor.gpio is None:
        raise SpecValidationError(
            f"Sensor {name!r}: kind {kind!r} requires a 'gpio' pin"
        )
    if kind == "fake" and sensor.value is None:
        raise SpecValidationError(
            f"Sensor {name!r}: kind 'fake' requires a constant 'value'"
        )
    if kind == "replay" and not sensor.csv:
        raise SpecValidationError(
            f"Sensor {name!r}: kind 'replay' requires a 'csv' path"
        )


def _build_namespace(spec: GrowSpec) -> set[str]:
    namespace = set(_BASE_NAMESPACE)
    namespace.update(stage.name for stage in spec.stages)
    return namespace


def _saturation_vapor_pressure_kpa(temp_c: float) -> float:
    """Tetens equation: saturation vapor pressure in kPa for `temp_c` in C."""
    return 0.6108 * math.exp(17.27 * temp_c / (temp_c + 237.3))


def _compute_vpd_kpa(temperature: TemperatureSetpoint, humidity_rh_target: float) -> float:
    temp_c = temperature.target
    if temperature.unit == "fahrenheit":
        temp_c = (temp_c - 32) * 5 / 9
    return _saturation_vapor_pressure_kpa(temp_c) * (1 - humidity_rh_target)


def _check_vpd_consistency(stage: Stage) -> None:
    if stage.vpd is None:
        return
    computed = _compute_vpd_kpa(
        stage.setpoints.temperature, stage.setpoints.humidity_rh.target
    )
    if abs(computed - stage.vpd.target) > stage.vpd.tolerance:
        raise SpecValidationError(
            f"Stage {stage.name!r}: declared VPD target {stage.vpd.target} "
            f"(tolerance {stage.vpd.tolerance}) is inconsistent with the "
            f"temperature/humidity setpoints, which imply a VPD of "
            f"{computed:.3f} kPa"
        )


def _check_exit_condition_threshold(stage: Stage) -> None:
    threshold = stage.exit_condition.threshold.strip()
    if not threshold.startswith(_COMPARISON_PREFIXES):
        # Treated as an enum/string literal, e.g. "starting_to_flatten".
        return
    if not _COMPARISON_THRESHOLD_RE.match(threshold):
        raise SpecValidationError(
            f"Stage {stage.name!r}: exit_condition.threshold "
            f"{stage.exit_condition.threshold!r} looks like a comparison but "
            f"could not be parsed as '<op> <number>'"
        )


def _check_controls_disabled(stage: Stage, spec: GrowSpec) -> None:
    for control in stage.controls_disabled:
        if control in _KNOWN_CONTROL_NAMES or control in spec.actuators:
            continue
        raise SpecValidationError(
            f"Stage {stage.name!r}: controls_disabled entry {control!r} is "
            f"not a known control and does not match any actuator defined "
            f"in 'actuators'"
        )
