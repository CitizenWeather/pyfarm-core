# pyfarm-core

Core spec schema and validation for `pyfarm` GrowSpec files.

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

## Development

```bash
pip install -e ".[dev]"
pytest
```
