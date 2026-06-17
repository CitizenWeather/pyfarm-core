# pyfarm-core

Core domain models and event infrastructure for PyFarm.

## What's here

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
