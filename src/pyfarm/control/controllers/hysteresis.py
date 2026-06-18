"""Bang-bang control with a deadband (tolerance)."""

from __future__ import annotations

from typing import Literal

from pyfarm.control.controllers.base import Controller
from pyfarm.control.engine.context import ControlContext

Direction = Literal["raise", "lower"]


class HysteresisController(Controller):
    def __init__(
        self,
        metric: str,
        direction: Direction = "raise",
        *,
        initial: bool = False,
    ) -> None:
        self.metric = metric
        self.direction = direction
        self._on = initial

    def compute(self, ctx: ControlContext) -> bool:
        reading = ctx.readings.get(self.metric)
        setpoint = self.setpoint(ctx)
        if reading is None or setpoint is None:
            self._on = False
            return False

        current = reading.value
        target = setpoint.target
        tolerance = getattr(setpoint, "tolerance", 0.0) or 0.0

        if self.direction == "raise":
            if current < target - tolerance:
                self._on = True
            elif current >= target:
                self._on = False
        else:
            if current > target + tolerance:
                self._on = True
            elif current <= target:
                self._on = False
        return self._on
