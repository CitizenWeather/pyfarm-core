# pyfarm-core

Core spec schema and validation for `pyfarm` GrowSpec files.

## What's here

- `pyfarm.control.spec` — Pydantic models for the GrowSpec YAML format, a YAML loader
  with environment-variable interpolation, and a cross-field validator (VPD consistency,
  exit-condition thresholds, alert/interlock expression safety, etc.)
- `pyfarm.control.expr` — `SafeExpressionEvaluator`, an AST-walking evaluator used to
  validate and evaluate alert and interlock expressions without `eval()`/`exec()`.

## Development

```bash
pip install -e ".[dev]"
pytest
```
