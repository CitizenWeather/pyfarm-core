import asyncio
from datetime import datetime, timezone

import pytest

from pyfarm.control.replay import ReplayExhausted, ReplaySensor
from pyfarm.control.sensors import SensorReadError, SensorReading


def _run(coro):
    return asyncio.run(coro)


def test_replays_readings_in_order():
    sensor = ReplaySensor("temperature", "celsius", [24.0, 24.5, 23.8])

    values = [_run(sensor.read()).value for _ in range(3)]

    assert values == [24.0, 24.5, 23.8]


def test_synthetic_timestamps_are_deterministic_and_increasing():
    sensor = ReplaySensor("temperature", "celsius", [1.0, 2.0])

    first = _run(sensor.read())
    second = _run(sensor.read())

    assert first.metric == "temperature"
    assert first.unit == "celsius"
    assert second.timestamp > first.timestamp


def test_raises_replay_exhausted_when_out_of_readings():
    sensor = ReplaySensor("temperature", "celsius", [24.0])

    _run(sensor.read())

    with pytest.raises(ReplayExhausted):
        _run(sensor.read())
    # ReplayExhausted is a SensorReadError so existing runner handling applies.
    assert issubclass(ReplayExhausted, SensorReadError)


def test_loop_wraps_back_to_start():
    sensor = ReplaySensor("temperature", "celsius", [1.0, 2.0], loop=True)

    values = [_run(sensor.read()).value for _ in range(5)]

    assert values == [1.0, 2.0, 1.0, 2.0, 1.0]


def test_remaining_counts_down():
    sensor = ReplaySensor("temperature", "celsius", [1.0, 2.0])

    assert sensor.remaining == 2
    _run(sensor.read())
    assert sensor.remaining == 1


def test_accepts_explicit_timestamp_tuples():
    ts = datetime(2026, 6, 15, tzinfo=timezone.utc)
    sensor = ReplaySensor("temperature", "celsius", [(ts, 21.0)])

    reading = _run(sensor.read())

    assert reading == SensorReading("temperature", 21.0, "celsius", ts)


def test_from_csv_reads_named_column(fixtures_dir):
    sensor = ReplaySensor.from_csv(
        fixtures_dir / "colonisation_sample.csv", "humidity_rh", "ratio"
    )

    first = _run(sensor.read())

    assert first.metric == "humidity_rh"
    assert first.value == pytest.approx(0.89)
    assert first.unit == "ratio"
    assert first.timestamp == datetime(2026, 1, 1, tzinfo=timezone.utc)
    assert sensor.remaining == 3


def test_from_csv_missing_column_raises(fixtures_dir):
    with pytest.raises(SensorReadError, match="no column 'pressure'"):
        ReplaySensor.from_csv(
            fixtures_dir / "colonisation_sample.csv", "pressure", "pa"
        )


def test_from_csv_missing_file_raises(tmp_path):
    with pytest.raises(SensorReadError, match="Could not read replay file"):
        ReplaySensor.from_csv(tmp_path / "nope.csv", "temperature", "celsius")
