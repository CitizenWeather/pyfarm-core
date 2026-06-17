"""The actuator interface the control engine commands."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ActuatorCommand:
    """A command for an actuator on a single tick.

    ``on`` is the relay/output state. ``duty`` is an optional 0-1 duty cycle for
    PWM-capable actuators; it is ignored by plain on/off relays.
    """

    on: bool
    duty: float | None = None

    def __post_init__(self) -> None:
        if self.duty is not None and not 0.0 <= self.duty <= 1.0:
            raise ValueError(f"duty {self.duty} must be between 0 and 1")

    @classmethod
    def off(cls) -> "ActuatorCommand":
        return cls(on=False)


@dataclass(frozen=True)
class ActuatorAction:
    """A record that an actuator applied a command at a point in time."""

    actuator: str
    command: ActuatorCommand
    timestamp: datetime
    reason: str | None = None


class Actuator(ABC):
    """Something the engine can switch on or off.

    Implementations name themselves via :attr:`name` and act on a
    :class:`ActuatorCommand` in :meth:`apply`. ``apply`` is async so commanding
    several outputs (GPIO, PWM, MQTT publishes) in one tick need not block.
    """

    name: str

    @abstractmethod
    async def apply(self, command: ActuatorCommand) -> None:
        """Drive the output to the state described by ``command``."""
        raise NotImplementedError

    async def off(self) -> None:
        """Convenience: command the actuator off (e.g. when an interlock trips)."""
        await self.apply(ActuatorCommand.off())
