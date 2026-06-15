import asyncio
from datetime import datetime, timedelta, timezone
from itertools import count

import pytest

from pyfarm.control.actuators import ActuatorCommand, LoggingActuator


def _run(coro):
    return asyncio.run(coro)


def _fixed_clock():
    base = datetime(2026, 6, 15, 14, 23, 0, tzinfo=timezone.utc)
    counter = count()
    return lambda: base + timedelta(seconds=next(counter))


def test_records_state_changes():
    actuator = LoggingActuator("misting", clock=_fixed_clock())

    _run(actuator.apply(ActuatorCommand(on=True)))
    _run(actuator.off())

    assert [(a.actuator, a.command.on) for a in actuator.history] == [
        ("misting", True),
        ("misting", False),
    ]


def test_coalesces_repeated_identical_commands():
    actuator = LoggingActuator("misting", clock=_fixed_clock())

    _run(actuator.apply(ActuatorCommand(on=True)))
    _run(actuator.apply(ActuatorCommand(on=True)))
    _run(actuator.apply(ActuatorCommand(on=True)))

    assert len(actuator.history) == 1


def test_coalesce_can_be_disabled():
    actuator = LoggingActuator("misting", clock=_fixed_clock(), coalesce=False)

    _run(actuator.apply(ActuatorCommand(on=True)))
    _run(actuator.apply(ActuatorCommand(on=True)))

    assert len(actuator.history) == 2


def test_is_on_reflects_last_command():
    actuator = LoggingActuator("heater", clock=_fixed_clock())

    assert actuator.is_on is False
    _run(actuator.apply(ActuatorCommand(on=True)))
    assert actuator.is_on is True
    _run(actuator.off())
    assert actuator.is_on is False


def test_records_reason_and_timestamp():
    actuator = LoggingActuator("misting", clock=_fixed_clock())

    _run(actuator.apply(ActuatorCommand(on=True), reason="RH 91% < 95%"))

    action = actuator.history[0]
    assert action.reason == "RH 91% < 95%"
    assert action.timestamp == datetime(2026, 6, 15, 14, 23, 0, tzinfo=timezone.utc)


def test_history_is_a_copy():
    actuator = LoggingActuator("misting", clock=_fixed_clock())
    _run(actuator.apply(ActuatorCommand(on=True)))

    actuator.history.clear()

    assert len(actuator.history) == 1


def test_command_rejects_out_of_range_duty():
    with pytest.raises(ValueError, match="duty"):
        ActuatorCommand(on=True, duty=1.5)
