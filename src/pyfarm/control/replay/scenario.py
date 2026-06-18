"""Offline replay: run the full control engine over pre-recorded CSV sensor data."""

from __future__ import annotations

from pathlib import Path

from pyfarm.control.actuators.logging import LoggingActuator
from pyfarm.control.engine.runner import ControlRunner
from pyfarm.control.sensors.replay import replay_sensors_from_csv
from pyfarm.control.spec.loader import load_spec


async def run_scenario(
    spec_path: str | Path,
    sensor_csv: str | Path,
    metrics: list[str] | None = None,
) -> ControlRunner:
    """Run the full control loop against pre-recorded sensor data.

    Returns the runner so callers can inspect actuator logs and event history.
    """
    spec = load_spec(spec_path)

    all_sensors = replay_sensors_from_csv(sensor_csv)
    sensors = (
        [s for s in all_sensors if s.metric in metrics]
        if metrics is not None
        else all_sensors
    )

    actuators = {name: LoggingActuator(name) for name in spec.actuators}

    runner = ControlRunner(spec, sensors, actuators, tick_seconds=0)
    await runner.run_until_exhausted()
    return runner
