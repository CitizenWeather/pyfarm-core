"""Load and validate GrowSpec YAML files."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import ValidationError

from pyfarm.core.config import MissingEnvVar, interpolate_env_vars
from pyfarm.control.exceptions import SpecValidationError
from pyfarm.control.spec.schema import GrowSpec
from pyfarm.control.spec.validator import validate_spec


def load_spec(path: str | Path) -> GrowSpec:
    """Load, parse, and validate a GrowSpec YAML file at ``path``.

    Environment variables referenced as ``${VAR_NAME}`` in string values are
    interpolated after YAML parsing. Raises :class:`SpecValidationError` if
    the file cannot be read, contains an unresolved environment variable,
    fails schema validation, or fails cross-field validation.
    """
    path = Path(path)
    try:
        raw = path.read_text()
    except OSError as exc:
        raise SpecValidationError(f"Could not read spec file {path}: {exc}") from exc

    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise SpecValidationError(f"Invalid YAML in {path}: {exc}") from exc

    try:
        data = interpolate_env_vars(data)
    except MissingEnvVar as exc:
        raise SpecValidationError(str(exc)) from exc

    try:
        spec = GrowSpec(**data)
    except ValidationError as exc:
        raise SpecValidationError(f"Invalid GrowSpec in {path}: {exc}") from exc

    validate_spec(spec)
    return spec
