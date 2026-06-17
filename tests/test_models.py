from datetime import datetime
from pyfarm.core.models import SensorReading, Unit, EventKind, ControlEvent


def test_sensor_reading_fields():
    r = SensorReading(value=22.5, unit=Unit.CELSIUS, timestamp=datetime.utcnow(), metric="temperature")
    assert r.value == 22.5
    assert r.unit == Unit.CELSIUS
    assert not r.stale


def test_control_event_defaults():
    e = ControlEvent(kind=EventKind.SYSTEM, message="hello")
    assert e.data == {}
    assert e.timestamp is not None
