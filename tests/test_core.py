"""Tests for pyfarm-core models and interfaces."""

import asyncio
from datetime import datetime, timezone

import pytest

from pyfarm.core.models import EventType, SensorReading, ActuatorState, ControlEvent
from pyfarm.core.actuator import Command, Actuator
from pyfarm.core.sensor import Sensor
from pyfarm.core.storage import NullStore, SnapshotStore


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
        state = ActuatorState(
            actuator_id="heater-1",
            command="set_temperature",
            value=25.0
        )
        assert state.actuator_id == "heater-1"
        assert state.command == "set_temperature"
        assert state.value == 25.0
        assert state.timestamp is not None

    def test_actuator_state_with_error(self):
        state = ActuatorState(
            actuator_id="heater-1",
            command="set_temperature",
            value=25.0,
            error="Power failure"
        )
        assert state.error == "Power failure"


class TestControlEvent:
    """Test ControlEvent dataclass."""

    def test_control_event_creation(self):
        event = ControlEvent(
            event_type=EventType.SENSOR_READING,
            grow_id="grow-1",
            metric="temperature",
            value=22.5
        )
        assert event.event_type == EventType.SENSOR_READING
        assert event.grow_id == "grow-1"
        assert event.metric == "temperature"
        assert event.value == 22.5
        assert event.severity == "info"

    def test_control_event_with_string_event_type(self):
        event = ControlEvent(
            event_type="alert",
            grow_id="grow-1",
            message="Temperature out of range"
        )
        assert event.event_type == EventType.ALERT
        assert isinstance(event.event_type, EventType)

    def test_control_event_severity_levels(self):
        severities = ["info", "warning", "alert", "critical"]
        for sev in severities:
            event = ControlEvent(
                event_type=EventType.ALERT,
                severity=sev
            )
            assert event.severity == sev


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


class MockActuator(Actuator):
    """Mock actuator for testing."""

    def __init__(self, actuator_id: str):
        super().__init__(actuator_id)
        self.state = "off"
        self.value = 0.0

    async def execute(self, command: Command):
        self.last_command = command
        self.state = command.command
        self.value = command.value
        return True

    async def get_state(self):
        return {"state": self.state, "value": self.value}


class TestActuatorInterface:
    """Test Actuator abstract class."""

    @pytest.mark.asyncio
    async def test_actuator_execute(self):
        actuator = MockActuator("heater-1")
        cmd = Command(actuator_id="heater-1", command="set_temp", value=25.0)
        result = await actuator.execute(cmd)
        assert result is True
        assert actuator.last_command == cmd

    @pytest.mark.asyncio
    async def test_actuator_get_state(self):
        actuator = MockActuator("fan-1")
        cmd = Command(actuator_id="fan-1", command="set_speed", value=75.0)
        await actuator.execute(cmd)
        state = await actuator.get_state()
        assert state["state"] == "set_speed"
        assert state["value"] == 75.0


class TestNullStore:
    """Test NullStore implementation."""

    def test_null_store_save(self):
        store = NullStore()
        # Should not raise any exception
        store.save_snapshot("grow-1", {"data": "test"})

    def test_null_store_load(self):
        store = NullStore()
        result = store.load_snapshot("grow-1")
        assert result is None

    def test_null_store_delete(self):
        store = NullStore()
        # Should not raise any exception
        store.delete_snapshot("grow-1")

    def test_null_store_is_snapshot_store(self):
        store = NullStore()
        assert isinstance(store, SnapshotStore)
