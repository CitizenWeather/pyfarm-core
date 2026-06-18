"""Actuator abstraction. Controllers compute commands; actuators apply them."""

from __future__ import annotations

import abc
from typing import Union

Command = Union[bool, float]


class Actuator(abc.ABC):
    def __init__(self, name: str) -> None:
        self.name = name

    @abc.abstractmethod
    async def apply(self, command: Command) -> None:
        raise NotImplementedError

    async def off(self) -> None:
        await self.apply(False)

    @staticmethod
    def is_on(command: Command) -> bool:
        if isinstance(command, bool):
            return command
        return float(command) > 0.0
