"""Tests for pyfarm-core models and interfaces."""

import asyncio
from datetime import datetime, timezone

import pytest

from pyfarm.core.models import (
    EventType,
    EventKind,
    SensorReading,
    ActuatorState,
    ControlEvent,
)
from pyfarm.core.actuator import Command, Actuator
from pyfarm.core.sensor import Sensor
from pyfarm.core.storage import NullBackend, StorageBackend


class TestEventType:
    """Test EventType enum."""

    def test_event_type_values(self):
        assert EventType.SENSOR_READING.value == "sensor_reading"
        assert EventType.ACTUATOR_COMMAND.value == "actuator_command"
        assert EventType.ALERT.value == "alert"
        assert EventType.STAGE_TRANSITION.value == "stage_transition"
        assert EventType.HEALTH_CHECK.value == "health_check"

    def test_event_type_from_string(self):
        assert EventType("sensor_reading") == EventType.SENSOR_READING
        assert EventType("alert") == EventType.ALERT


class TestSensorReading:
    """Test SensorReading dataclass."""

    def test_sensor_reading_creation(self):
        reading = SensorReading(
            metric="temperature",
            value=22.5,
            unit="°C",
            sensor_id="temp-1"
        )
        assert reading.metric == "temperature"
        assert reading.value == 22.5
        assert reading.unit == "°C"
        assert reading.sensor_id == "temp-1"
        assert reading.timestamp is not None
        assert reading.error is None

    def test_sensor_reading_requires_metric(self):
        with pytest.raises(ValueError, match="metric is required"):
            SensorReading(value=22.5, unit="°C")

    def test_sensor_reading_with_error(self):
        reading = SensorReading(
            metric="temperature",
            value=0.0,
            unit="°C",
            error="Sensor timeout"
        )
        assert reading.error == "Sensor timeout"


class TestActuatorState:
    """Test ActuatorState dataclass."""

    def test_actuator_state_creation(self):
        state = ActuatorState(name="heater-1", state=True)
        assert state.name == "heater-1"
        assert state.state is True
        assert state.timestamp is not None
        assert state.last_toggled_at is None

    def test_actuator_state_off(self):
        toggled = datetime.now(timezone.utc)
        state = ActuatorState(name="fan-1", state=False, last_toggled_at=toggled)
        assert state.state is False
        assert state.last_toggled_at == toggled


class TestControlEvent:
    """Test ControlEvent dataclass."""

    def test_control_event_creation(self):
        event = ControlEvent(
            kind=EventKind.SYSTEM,
            message="runner started",
            data={"grow_id": "grow-1"},
        )
        assert event.kind == EventKind.SYSTEM
        assert event.message == "runner started"
        assert event.data == {"grow_id": "grow-1"}
        assert event.timestamp is not None

    def test_control_event_with_string_kind(self):
        event = ControlEvent(kind="alert_fired", message="out of range")
        assert event.kind == EventKind.ALERT_FIRED
        assert isinstance(event.kind, EventKind)

    def test_control_event_defaults(self):
        event = ControlEvent(kind=EventKind.SENSOR_FAILURE)
        assert event.message == ""
        assert event.data == {}


class TestCommandDataclass:
    """Test Command dataclass."""

    def test_command_creation(self):
        cmd = Command(
            actuator_id="fan-1",
            command="set_speed",
            value=50.0
        )
        assert cmd.actuator_id == "fan-1"
        assert cmd.command == "set_speed"
        assert cmd.value == 50.0
        assert cmd.duration_seconds is None

    def test_command_with_duration(self):
        cmd = Command(
            actuator_id="light-1",
            command="on",
            value=1.0,
            duration_seconds=3600.0
        )
        assert cmd.duration_seconds == 3600.0


class MockSensor(Sensor):
    """Mock sensor for testing."""

    def __init__(self, sensor_id: str, metric: str, unit: str, healthy: bool = True):
        super().__init__(sensor_id, metric, unit)
        self.healthy = healthy

    async def read(self):
        if not self.healthy:
            return SensorReading(metric=self.metric, error="Sensor error")
        return SensorReading(
            metric=self.metric,
            value=20.0,
            unit=self.unit,
            sensor_id=self.sensor_id
        )

    async def check_health(self):
        return self.healthy


class TestSensorInterface:
    """Test Sensor abstract class."""

    @pytest.mark.asyncio
    async def test_sensor_read(self):
        sensor = MockSensor("temp-1", "temperature", "°C")
        reading = await sensor.read()
        assert reading.metric == "temperature"
        assert reading.value == 20.0
        assert reading.unit == "°C"

    @pytest.mark.asyncio
    async def test_sensor_health_check(self):
        healthy_sensor = MockSensor("temp-1", "temperature", "°C", healthy=True)
        assert await healthy_sensor.check_health() is True

        broken_sensor = MockSensor("temp-1", "temperature", "°C", healthy=False)
        assert await broken_sensor.check_health() is False

    def test_sensor_not_exhausted_by_default(self):
        sensor = MockSensor("temp-1", "temperature", "°C")
        assert sensor.exhausted is False


class MockActuator(Actuator):
    """Mock actuator for testing the on()/off() canonical interface."""

    def __init__(self, actuator_id: str):
        super().__init__(actuator_id)
        self.is_on = False

    async def on(self):
        self.is_on = True

    async def off(self):
        self.is_on = False


class TestActuatorInterface:
    """Test Actuator abstract class."""

    @pytest.mark.asyncio
    async def test_actuator_on_off(self):
        actuator = MockActuator("heater-1")
        assert actuator.is_on is False
        await actuator.on()
        assert actuator.is_on is True
        await actuator.off()
        assert actuator.is_on is False

    @pytest.mark.asyncio
    async def test_actuator_execute_delegates_to_on_off(self):
        actuator = MockActuator("fan-1")
        cmd = Command(actuator_id="fan-1", command="on", value=1.0)
        result = await actuator.execute(cmd)
        assert result is True
        assert actuator.is_on is True
        assert actuator.last_command == cmd

        await actuator.execute(Command(actuator_id="fan-1", command="off"))
        assert actuator.is_on is False

    @pytest.mark.asyncio
    async def test_actuator_get_state(self):
        actuator = MockActuator("fan-1")
        state = await actuator.get_state()
        assert state["actuator_id"] == "fan-1"


class TestNullBackend:
    """Test NullBackend implementation of the StorageBackend protocol."""

    @pytest.mark.asyncio
    async def test_null_backend_write_snapshot(self):
        backend = NullBackend()
        # Should not raise
        await backend.write_snapshot({"data": "test"})

    @pytest.mark.asyncio
    async def test_null_backend_get_latest_snapshot(self):
        backend = NullBackend()
        assert await backend.get_latest_snapshot("grow-1") is None

    @pytest.mark.asyncio
    async def test_null_backend_readings_empty(self):
        backend = NullBackend()
        await backend.insert_sensor_reading(
            SensorReading(metric="temperature", value=20.0, sensor_id="temp-1")
        )
        readings = await backend.get_readings(
            "temp-1",
            datetime(2020, 1, 1, tzinfo=timezone.utc),
            datetime(2030, 1, 1, tzinfo=timezone.utc),
        )
        assert readings == []

    @pytest.mark.asyncio
    async def test_null_backend_close(self):
        backend = NullBackend()
        await backend.close()

    def test_null_backend_satisfies_protocol(self):
        backend = NullBackend()
        assert isinstance(backend, StorageBackend)
