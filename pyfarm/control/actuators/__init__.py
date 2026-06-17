"""Actuator abstractions for the control engine.

An :class:`Actuator` is the only thing the engine commands. Real relays/PWM
outputs and the hardware-free
:class:`~pyfarm.control.actuators.logging.LoggingActuator` implement the same
interface, so the runner can drive real hardware or simply record what it
*would* have done.
"""

from pyfarm.control.actuators.base import Actuator, ActuatorAction, ActuatorCommand
from pyfarm.control.actuators.logging import LoggingActuator

__all__ = [
    "Actuator",
    "ActuatorAction",
    "ActuatorCommand",
    "LoggingActuator",
]
