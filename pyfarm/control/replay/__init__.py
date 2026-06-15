"""Replay / simulation support: drive the engine from recorded data.

Because the runner takes its sensors and actuators as injected dependencies, a
recorded CSV of readings (:class:`~pyfarm.control.replay.fake_sensor.ReplaySensor`)
and a recording actuator (:class:`~pyfarm.control.actuators.logging.LoggingActuator`)
let a contributor run the full control loop with no hardware — for tests, CI, a
playground, or a "what would it have done?" demo.
"""

from pyfarm.control.replay.fake_sensor import ReplayExhausted, ReplaySensor

__all__ = ["ReplayExhausted", "ReplaySensor"]
