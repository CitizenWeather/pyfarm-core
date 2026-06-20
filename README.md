# pyfarm-core

Shared base models, event bus, and protocols for the pyfarm ecosystem.

## Purpose

Common type system and protocols that all pyfarm modules depend on. Enables:
- Consistent sensor/actuator interfaces
- Shared event models for control loop
- Standard error types
- Persistence abstraction

## Core Modules

- **models.py** — `SensorReading`, `ActuatorState`, `ControlEvent`
- **errors.py** — Standard error types
- **sensor.py** — Base `Sensor` class
- **actuator.py** — Base `Actuator` class and `Command` type
- **storage.py** — `SnapshotStore` abstraction

## Integration

All other pyfarm modules import from pyfarm-core for type definitions and base classes.
