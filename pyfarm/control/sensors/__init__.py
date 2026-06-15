"""Sensor abstractions for the control engine.

A :class:`Sensor` is the only thing the engine reads from. Real hardware
sensors and the hardware-free :class:`~pyfarm.control.replay.fake_sensor.ReplaySensor`
implement the same interface, so the same runner can drive a live tent or a
recorded dataset.
"""

from pyfarm.control.sensors.base import (
    Sensor,
    SensorReadError,
    SensorReading,
)

__all__ = ["Sensor", "SensorReadError", "SensorReading"]
