import pytest
from pydantic import ValidationError

from pyfarm.control.spec.schema import (
    ActuatorSpec,
    Duration,
    GrowSpec,
    LightSetpoint,
    Metadata,
    Setpoints,
    Stage,
)

VALID_SETPOINTS = {
    "temperature": {"target": 24.0, "unit": "celsius", "tolerance": 2.0},
    "humidity_rh": {"target": 0.9, "tolerance": 0.05},
    "co2_ppm": {"target": 2000, "tolerance": 500},
    "light": {"schedule": "0/24"},
}

VALID_STAGE = {
    "name": "colonisation",
    "duration": {"min_days": 14, "max_days": 28},
    "exit_condition": {"metric": "visual.colonisation_pct", "threshold": ">= 0.95"},
    "setpoints": VALID_SETPOINTS,
}

VALID_METADATA = {
    "name": "oyster-coffee-grounds-fruiting",
    "species": "pleurotus.ostreatus",
    "substrate": "coffee_grounds_supplemented",
    "author": "someone@example.com",
    "registry": "pyfarm/community/fungi/oyster-classic-v3",
}


def test_setpoints_round_trip() -> None:
    setpoints = Setpoints(**VALID_SETPOINTS)
    assert setpoints.temperature.target == 24.0
    assert setpoints.humidity_rh.tolerance == 0.05
    assert setpoints.light.schedule == "0/24"


def test_stage_round_trip() -> None:
    stage = Stage(**VALID_STAGE)
    assert stage.name == "colonisation"
    assert stage.duration.min_days == 14
    assert stage.controls_disabled == []
    assert stage.vpd is None


def test_minimal_grow_spec_round_trip() -> None:
    spec = GrowSpec(
        spec_version="1.0",
        kind="GrowSpec",
        metadata=VALID_METADATA,
        stages=[VALID_STAGE],
    )
    assert spec.metadata.species == "pleurotus.ostreatus"
    assert spec.alerts == []
    assert spec.actuators == {}


def test_extra_fields_rejected_on_metadata() -> None:
    with pytest.raises(ValidationError):
        Metadata(**VALID_METADATA, extra_field="nope")


def test_extra_fields_rejected_on_stage() -> None:
    bad_stage = dict(VALID_STAGE, unexpected="field")
    with pytest.raises(ValidationError):
        Stage(**bad_stage)


def test_duration_rejects_max_less_than_min() -> None:
    with pytest.raises(ValidationError):
        Duration(min_days=10, max_days=5)


def test_duration_allows_equal_min_and_max() -> None:
    duration = Duration(min_days=5, max_days=5)
    assert duration.min_days == duration.max_days == 5


def test_negative_tolerance_rejected() -> None:
    bad_setpoints = dict(VALID_SETPOINTS)
    bad_setpoints["humidity_rh"] = {"target": 0.9, "tolerance": -0.1}
    with pytest.raises(ValidationError):
        Setpoints(**bad_setpoints)


def test_humidity_rh_out_of_range_rejected() -> None:
    bad_setpoints = dict(VALID_SETPOINTS)
    bad_setpoints["humidity_rh"] = {"target": 90, "tolerance": 5}
    with pytest.raises(ValidationError):
        Setpoints(**bad_setpoints)


def test_light_schedule_must_sum_to_24() -> None:
    with pytest.raises(ValidationError):
        LightSetpoint(schedule="12/10")


def test_light_schedule_must_match_format() -> None:
    with pytest.raises(ValidationError):
        LightSetpoint(schedule="always-on")


def test_gpio_out_of_range_rejected() -> None:
    with pytest.raises(ValidationError):
        ActuatorSpec(kind="relay", gpio=99)


def test_unsupported_spec_version_rejected() -> None:
    with pytest.raises(ValidationError):
        GrowSpec(
            spec_version="2.0",
            kind="GrowSpec",
            metadata=VALID_METADATA,
            stages=[VALID_STAGE],
        )


def test_empty_stages_rejected() -> None:
    with pytest.raises(ValidationError):
        GrowSpec(
            spec_version="1.0",
            kind="GrowSpec",
            metadata=VALID_METADATA,
            stages=[],
        )


def test_duplicate_stage_names_rejected() -> None:
    with pytest.raises(ValidationError):
        GrowSpec(
            spec_version="1.0",
            kind="GrowSpec",
            metadata=VALID_METADATA,
            stages=[VALID_STAGE, VALID_STAGE],
        )
