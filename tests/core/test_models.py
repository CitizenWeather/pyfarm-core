from datetime import datetime, timedelta, timezone

from pyfarm.core.models import ActuatorState, ControlEvent, EventKind, SensorReading, Unit


def test_sensor_reading_stale_when_old():
    old_ts = datetime.now(timezone.utc) - timedelta(seconds=60)
    reading = SensorReading(value=22.0, unit=Unit.CELSIUS, timestamp=old_ts, metric="temperature")
    assert reading.stale is True


def test_sensor_reading_not_stale_when_recent():
    reading = SensorReading(
        value=22.0, unit=Unit.CELSIUS,
        timestamp=datetime.now(timezone.utc),
        metric="temperature",
    )
    assert reading.stale is False


def test_sensor_reading_stale_handles_naive_timestamp():
    old_ts = datetime.utcnow() - timedelta(seconds=60)
    reading = SensorReading(value=22.0, unit=Unit.CELSIUS, timestamp=old_ts, metric="temperature")
    assert reading.stale is True


def test_control_event_defaults():
    ev = ControlEvent(kind=EventKind.ALERT_FIRED, message="too hot")
    assert ev.kind == EventKind.ALERT_FIRED
    assert ev.message == "too hot"
    assert ev.data == {}
    assert ev.timestamp is not None


def test_control_event_with_data():
    ev = ControlEvent(kind=EventKind.STAGE_TRANSITION, message="moved to stage 2", data={"stage": 2})
    assert ev.data == {"stage": 2}


def test_actuator_state_fields():
    state = ActuatorState(name="fan", state=True)
    assert state.name == "fan"
    assert state.state is True
    assert state.last_toggled_at is None


def test_event_kind_values():
    assert EventKind.SYSTEM == "system"
    assert EventKind.ALERT_FIRED == "alert_fired"
    assert EventKind.STAGE_TRANSITION == "stage_transition"
    assert EventKind.SENSOR_FAILURE == "sensor_failure"
