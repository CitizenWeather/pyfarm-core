from pathlib import Path

import pytest

from pyfarm.control.spec.exceptions import SpecValidationError
from pyfarm.control.spec.loader import load_spec

FIXTURE_PATH = Path(__file__).resolve().parents[2] / "fixtures" / "oyster_fruiting.pyfarm.yaml"


@pytest.fixture(autouse=True)
def telegram_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "test-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "test-chat-id")


def test_load_spec_end_to_end() -> None:
    spec = load_spec(FIXTURE_PATH)

    assert spec.spec_version == "1.0"
    assert spec.metadata.name == "oyster-coffee-grounds-fruiting"
    assert [stage.name for stage in spec.stages] == [
        "colonisation",
        "initiation",
        "fruiting",
    ]
    assert spec.stages[1].vpd is not None
    assert spec.actuators["misting"].gpio == 17
    assert len(spec.alerts) == 3


def test_load_spec_interpolates_env_vars() -> None:
    spec = load_spec(FIXTURE_PATH)

    telegram = spec.notifications.channels["telegram"]
    assert telegram["bot_token"] == "test-token"
    assert telegram["chat_id"] == "test-chat-id"


def test_load_spec_missing_env_var_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)

    with pytest.raises(SpecValidationError, match="TELEGRAM_BOT_TOKEN"):
        load_spec(FIXTURE_PATH)


def test_load_spec_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(SpecValidationError, match="Could not read"):
        load_spec(tmp_path / "does_not_exist.yaml")


def test_load_spec_invalid_yaml_raises(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.yaml"
    bad_file.write_text("spec_version: '1.0'\nkind: [unbalanced\n")

    with pytest.raises(SpecValidationError, match="Invalid YAML"):
        load_spec(bad_file)


def test_load_spec_schema_validation_error(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad_schema.yaml"
    bad_file.write_text("spec_version: '1.0'\nkind: NotAGrowSpec\nmetadata: {}\nstages: []\n")

    with pytest.raises(SpecValidationError, match="Invalid GrowSpec"):
        load_spec(bad_file)
