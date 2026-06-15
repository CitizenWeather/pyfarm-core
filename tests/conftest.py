from pathlib import Path

import pytest


@pytest.fixture
def fixtures_dir() -> Path:
    return Path(__file__).resolve().parent / "fixtures"


@pytest.fixture
def oyster_fruiting_spec_path(fixtures_dir: Path) -> Path:
    return fixtures_dir / "oyster_fruiting.pyfarm.yaml"
