"""Load and validate GrowSpec YAML files."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from pydantic import ValidationError

from pyfarm.control.exceptions import SpecValidationError
from pyfarm.control.spec.schema import GrowSpec
from pyfarm.control.spec.validator import validate_spec

_ENV_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


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

    data = _interpolate_env_vars(data)

    try:
        spec = GrowSpec(**data)
    except ValidationError as exc:
        raise SpecValidationError(f"Invalid GrowSpec in {path}: {exc}") from exc

    validate_spec(spec)
    return spec


def _interpolate_env_vars(value: Any) -> Any:
    if isinstance(value, str):
        return _ENV_VAR_RE.sub(_replace_env_var, value)
    if isinstance(value, dict):
        return {key: _interpolate_env_vars(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_interpolate_env_vars(item) for item in value]
    return value


def _replace_env_var(match: re.Match[str]) -> str:
    name = match.group(1)
    value = os.environ.get(name)
    if value is None:
        raise SpecValidationError(
            f"Environment variable {name!r} referenced as "
            f"'${{{name}}}' is not set"
        )
    return value
