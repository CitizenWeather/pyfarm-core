import copy
from pathlib import Path

import pytest
import yaml

from pyfarm.control.exceptions import SpecValidationError
from pyfarm.control.spec.schema import GrowSpec
from pyfarm.control.spec.validator import validate_spec


@pytest.fixture
def spec_data(
    monkeypatch: pytest.MonkeyPatch, oyster_fruiting_spec_path: Path
) -> dict:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test-chat-id")
    raw = oyster_fruiting_spec_path.read_text()
    raw = raw.replace("${TELEGRAM_BOT_TOKEN}", "test-token")
    raw = raw.replace("${TELEGRAM_CHAT_ID}", "test-chat-id")
    return yaml.safe_load(raw)


def test_valid_fixture_passes(spec_data: dict) -> None:
    spec = GrowSpec(**spec_data)
    validate_spec(spec)


def test_vpd_inconsistency_rejected(spec_data: dict) -> None:
    data = copy.deepcopy(spec_data)
    initiation = next(s for s in data["stages"] if s["name"] == "initiation")
    initiation["vpd"]["target"] = 0.4  # inconsistent with 18C / 95% RH (~0.10 kPa)

    spec = GrowSpec(**data)
    with pytest.raises(SpecValidationError, match="VPD"):
        validate_spec(spec)


def test_unknown_variable_in_alert_condition_rejected(spec_data: dict) -> None:
    data = copy.deepcopy(spec_data)
    data["alerts"][0]["condition"] = "pressure.current > 28"

    spec = GrowSpec(**data)
    with pytest.raises(SpecValidationError, match="unknown variable"):
        validate_spec(spec)


def test_unsafe_interlock_expression_rejected(spec_data: dict) -> None:
    data = copy.deepcopy(spec_data)
    data["actuators"]["misting"]["interlock"] = "__import__('os').system('ls')"

    spec = GrowSpec(**data)
    with pytest.raises(SpecValidationError, match="misting"):
        validate_spec(spec)


def test_malformed_comparison_threshold_rejected(spec_data: dict) -> None:
    data = copy.deepcopy(spec_data)
    colonisation = next(s for s in data["stages"] if s["name"] == "colonisation")
    colonisation["exit_condition"]["threshold"] = ">= not-a-number"

    spec = GrowSpec(**data)
    with pytest.raises(SpecValidationError, match="threshold"):
        validate_spec(spec)


def test_enum_threshold_is_allowed(spec_data: dict) -> None:
    data = copy.deepcopy(spec_data)
    fruiting = next(s for s in data["stages"] if s["name"] == "fruiting")
    assert fruiting["exit_condition"]["threshold"] == "starting_to_flatten"

    spec = GrowSpec(**data)
    validate_spec(spec)  # should not raise


def test_unknown_controls_disabled_entry_rejected(spec_data: dict) -> None:
    data = copy.deepcopy(spec_data)
    colonisation = next(s for s in data["stages"] if s["name"] == "colonisation")
    colonisation["controls_disabled"] = ["not_a_real_control"]

    spec = GrowSpec(**data)
    with pytest.raises(SpecValidationError, match="controls_disabled"):
        validate_spec(spec)


def test_controls_disabled_can_reference_actuator(spec_data: dict) -> None:
    data = copy.deepcopy(spec_data)
    colonisation = next(s for s in data["stages"] if s["name"] == "colonisation")
    colonisation["controls_disabled"] = ["misting", "FAE", "heater"]

    spec = GrowSpec(**data)
    validate_spec(spec)  # "heater" is a defined actuator
