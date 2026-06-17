# pyfarm-core

Core domain models and event infrastructure for PyFarm.

## What's here

- `pyfarm.control.spec` — Pydantic models for the GrowSpec YAML format, a YAML loader
  with environment-variable interpolation, and a cross-field validator (VPD consistency,
  exit-condition thresholds, alert/interlock expression safety, etc.)
- `pyfarm.control.expr` — `SafeExpressionEvaluator`, an AST-walking evaluator used to
  validate and evaluate alert and interlock expressions without `eval()`/`exec()`.
- `pyfarm.control.sensors` / `pyfarm.control.actuators` — the `Sensor` and `Actuator`
  interfaces the engine reads from and commands. Real hardware and simulated leaves
  implement the same interface, so one runner can drive a live tent or a recording.
- `pyfarm.control.replay` — `ReplaySensor` replays a recorded series of readings (or a
  CSV) and `LoggingActuator` records what the engine *would* have done. Together they
  let the full control loop run with no hardware — for tests, CI, and contributor demos.
- **`pyfarm.core.models`** — Domain model types used across PyFarm
  - `SensorReading` - timestamped sensor value with metric name and unit
  - `ControlEvent` - log entry for control loop events
  - `ActuatorState` - current state of an actuator
  - `EventKind` and `Unit` - enums for event types and sensor units
  
- **`pyfarm.core.events`** — Event distribution infrastructure
  - `EventBus` - sync-emit, async-fan-out event spine
  - `EventSink` - protocol for event subscribers (e.g., persistence, notifications)

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
