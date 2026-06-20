"""Core error types for pyfarm."""


class PyFarmError(Exception):
    """Base error for all pyfarm exceptions."""
    pass


class ControlError(PyFarmError):
    """Error in control loop execution."""
    pass


class SensorReadError(PyFarmError):
    """Error reading from a sensor."""
    pass


class ReplayExhausted(PyFarmError):
    """Replay log has no more events."""
    pass


class ValidationError(PyFarmError):
    """Schema or data validation failed."""
    pass


class ConfigError(PyFarmError):
    """Configuration error."""
    pass
