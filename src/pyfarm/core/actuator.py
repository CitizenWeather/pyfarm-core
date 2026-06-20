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
    """Base class for all actuators."""

    def __init__(self, actuator_id: str):
        self.actuator_id = actuator_id
        self.last_command: Optional[Command] = None

    @abstractmethod
    async def execute(self, command: Command) -> bool:
        """Execute a command on this actuator. Return True if successful."""
        pass

    @abstractmethod
    async def get_state(self) -> Any:
        """Get current state of the actuator."""
        pass
