from datetime import datetime, timedelta, timezone

from pyfarm.core.models import ActuatorState, ControlEvent, SensorReading


def test_sensor_reading_defaults_timestamp():
    r = SensorReading(value=21.0, unit="celsius")
    assert r.value == 21.0
    assert r.timestamp.tzinfo is not None


def test_flatline_minutes():
    now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    changed = now - timedelta(minutes=5)
    r = SensorReading(value=1.0, unit="")
    assert r.flatline_minutes(value_changed_at=changed, now=now) == 5.0


def test_actuator_state_seconds_in_state():
    now = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    st = ActuatorState(name="fan", last_changed=now - timedelta(seconds=30))
    assert st.seconds_in_state(now=now) == 30.0


def test_control_event_kind_is_free_string():
    ev = ControlEvent(kind="custom_kind", message="hi")
    assert ev.kind == "custom_kind"
    assert ev.data == {}
