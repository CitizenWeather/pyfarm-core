# pyfarm-core

Core domain models and event infrastructure for PyFarm.

## What's here

- **`pyfarm.core.models`** — the canonical domain value types every PyFarm package
  speaks: `SensorReading`, `ActuatorState`, `ControlEvent`, plus the `EventKind` and
  `Unit` enums.
- **`pyfarm.core.events`** — event distribution: `EventBus` (sync-emit, async-fan-out)
  and the `EventSink` protocol for subscribers (persistence, notifications).
- **`pyfarm.core.sensor` / `pyfarm.core.actuator`** — the `Sensor` and `Actuator`
  contracts the engine reads from and commands. Real hardware and simulated/replay
  leaves implement the same interface, so one runner can drive a live tent or a
  recording. (Concrete drivers ship in `pyfarm-control` today; `pyfarm-iot` later.)
- **`pyfarm.core.storage`** — the `SnapshotStore` persistence abstraction (+ `NullStore`).
  Concrete stores that know the full `ControlContext` (`JsonSnapshotStore`, `SQLiteStore`)
  live in `pyfarm-control` and subclass it.
- **`pyfarm.core.config`** — `${VAR}` interpolation (the spec loader delegates to it) and
  named environment profiles for secrets/credentials.
- **`pyfarm.core.errors`** — the runtime error hierarchy (`ControlError`,
  `SensorReadError`, `ReplayExhausted`).
- `pyfarm.control.spec` — Pydantic models for the GrowSpec YAML format, a YAML loader
  with environment-variable interpolation, and a cross-field validator.
- `pyfarm.control.expr` — `SafeExpressionEvaluator`, an AST-walking evaluator for alert
  and interlock expressions without `eval()`/`exec()`.

## Usage

This package is imported by `pyfarm-control` and `pyfarm-cli`. It's also the foundation for building custom extensions (custom sensors, actuators, notifiers).

### Creating a Custom EventSink

```python
from pyfarm.core.events import EventSink
from pyfarm.core.models import ControlEvent, EventKind

class MyNotifier(EventSink):
    async def handle(self, event: ControlEvent) -> None:
        if event.kind == EventKind.ALERT_FIRED:
            await self.send_alert(event.message)
    
    async def send_alert(self, message: str):
        # Your logic here
        pass

# Subscribe to events
from pyfarm.control.engine.runner import ControlRunner
runner = ControlRunner(..., event_sinks=[MyNotifier()])
```

## Development

```bash
pip install -e ".[dev]"
pytest
```
