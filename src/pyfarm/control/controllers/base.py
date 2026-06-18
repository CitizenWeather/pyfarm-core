"""Controllers decide what an actuator should do, given the live context."""

from __future__ import annotations

import abc

from pyfarm.control.actuators.base import Command
from pyfarm.control.engine.context import ControlContext

_SETPOINT_ATTR = {
    "temperature": "temperature",
    "humidity_rh": "humidity_rh",
    "co2_ppm": "co2_ppm",
}


class Controller(abc.ABC):
    metric: str | None = None

    @abc.abstractmethod
    def compute(self, ctx: ControlContext) -> Command:
        raise NotImplementedError

    def setpoint(self, ctx: ControlContext):
        """Return the current stage's setpoint for self.metric, or None."""
        if self.metric is None:
            return None
        attr = _SETPOINT_ATTR.get(self.metric)
        if attr is None:
            return None
        # BaseStage may not have setpoints; guard with getattr
        setpoints = getattr(ctx.current_stage, "setpoints", None)
        if setpoints is None:
            return None
        return getattr(setpoints, attr, None)
