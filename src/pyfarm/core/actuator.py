"""Actuator protocol for pyfarm."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class Command:
    """A command to execute on an actuator."""
    actuator_id: str
    command: str
    value: float = 0.0
    duration_seconds: Optional[float] = None


class Actuator(ABC):
    """
    Base class for all actuators.

    Canonical interface: on() / off() (used by control runner).
    execute(Command) / get_state() are available for advanced use but implemented
    via on/off semantics.
    """

    def __init__(self, actuator_id: str):
        self.actuator_id = actuator_id
        self.last_command: Optional[Command] = None

    @abstractmethod
    async def on(self) -> None:
        """Turn on (or engage) the actuator."""
        pass

    @abstractmethod
    async def off(self) -> None:
        """Turn off (or disengage) the actuator."""
        pass

    async def execute(self, command: Command) -> bool:
        """
        High-level command interface (for backward compat / advanced use).
        Default: interprets command.command as "on" or "off", delegates to on()/off().
        Override for complex multi-state actuators.
        """
        self.last_command = command
        if command.command.lower() in ("on", "true", "1"):
            await self.on()
        elif command.command.lower() in ("off", "false", "0"):
            await self.off()
        else:
            # Fall through to subclass if not a simple on/off
            raise NotImplementedError(f"Command '{command.command}' not understood by base Actuator")
        return True

    async def get_state(self) -> Any:
        """
        Query actuator state (for backward compat / introspection).
        Default: returns actuator_id. Override for detailed state reporting.
        """
        return {"actuator_id": self.actuator_id}
