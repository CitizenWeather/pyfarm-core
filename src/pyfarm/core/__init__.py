"""pyfarm-core: shared domain models, contracts and infrastructure for PyFarm.

This is the foundation every other PyFarm package builds on:

* :mod:`pyfarm.core.models` — ``SensorReading``, ``ActuatorState``, ``ControlEvent``
* :mod:`pyfarm.core.events` — ``EventBus`` / ``EventSink``
* :mod:`pyfarm.core.sensor` / :mod:`pyfarm.core.actuator` — the driver contracts
* :mod:`pyfarm.core.storage` — the ``SnapshotStore`` persistence abstraction
* :mod:`pyfarm.core.config` — env interpolation and environment profiles
* :mod:`pyfarm.core.errors` — the runtime error hierarchy

The GrowSpec schema, loader and expression evaluator live under the
``pyfarm.control.spec`` / ``pyfarm.control.expr`` namespace, also shipped by
this package.
"""

from pyfarm.core.events import EventBus, EventSink
from pyfarm.core.models import (
    ActuatorState,
    ControlEvent,
    EventKind,
    SensorReading,
    Unit,
)

__all__ = [
    "EventBus",
    "EventSink",
    "SensorReading",
    "ActuatorState",
    "ControlEvent",
    "EventKind",
    "Unit",
]
