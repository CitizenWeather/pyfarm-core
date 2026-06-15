"""An actuator that records commands instead of touching hardware."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone

from pyfarm.control.actuators.base import Actuator, ActuatorAction, ActuatorCommand


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


class LoggingActuator(Actuator):
    """Records every command it receives rather than driving real hardware.

    This is the counterpart to
    :class:`~pyfarm.control.replay.fake_sensor.ReplaySensor`: together they let
    the full control loop run with no GPIO, producing a log of what the engine
    *would* have done ("would have fired misting at 14:23:05"). It also makes
    deterministic integration tests possible by injecting a fixed clock.
    """

    def __init__(
        self,
        name: str,
        *,
        clock: Callable[[], datetime] = _utcnow,
        coalesce: bool = True,
    ) -> None:
        self.name = name
        self._clock = clock
        self._coalesce = coalesce
        self._history: list[ActuatorAction] = []

    async def apply(self, command: ActuatorCommand, reason: str | None = None) -> None:
        if self._coalesce and self._history:
            last = self._history[-1].command
            if last == command:
                # No state change — don't spam the log with identical ticks.
                return
        self._history.append(
            ActuatorAction(self.name, command, self._clock(), reason)
        )

    async def off(self) -> None:
        await self.apply(ActuatorCommand.off())

    @property
    def history(self) -> list[ActuatorAction]:
        """All recorded state changes, in order."""
        return list(self._history)

    @property
    def is_on(self) -> bool:
        """The last commanded on/off state (defaults to off before any command)."""
        return bool(self._history) and self._history[-1].command.on
