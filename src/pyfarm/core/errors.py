"""Runtime error hierarchy shared across PyFarm.

Spec *loading* errors live in :class:`pyfarm.control.exceptions.SpecValidationError`.
These are the *runtime* counterparts raised while a grow is running, owned here
in core so drivers (sensors/actuators) and the engine raise and catch the same
types.
"""

from __future__ import annotations


class ControlError(Exception):
    """Base class for control-engine runtime errors."""


class SensorReadError(ControlError):
    """Raised when a sensor cannot produce a reading.

    The runner catches this and degrades gracefully (hold the last known value,
    raise an alert) rather than crashing the whole grow.
    """


class ReplayExhausted(ControlError):
    """Raised by replay sensors when the recorded data is exhausted."""
