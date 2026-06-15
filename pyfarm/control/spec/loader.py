"""Load and validate GrowSpec YAML files."""

from __future__ import annotations

import os
import re
from pathlib import Path

import yaml
from pydantic import ValidationError

from pyfarm.control.spec.exceptions import SpecValidationError
from pyfarm.control.spec.schema import GrowSpec
from pyfarm.control.spec.validator import validate_spec

_ENV_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


def load_spec(path: str | Path) -> GrowSpec:
    """Load, parse, and validate a GrowSpec YAML file at ``path``.

    Environment variables referenced as ``${VAR_NAME}`` are interpolated
    before parsing. Raises :class:`SpecValidationError` if the file cannot be
    read, contains an unresolved environment variable, fails schema
    validation, or fails cross-field validation.
    """
    path = Path(path)
    try:
        raw = path.read_text()
    except OSError as exc:
        raise SpecValidationError(f"Could not read spec file {path}: {exc}") from exc

    interpolated = _interpolate_env_vars(raw)

    try:
        data = yaml.safe_load(interpolated)
    except yaml.YAMLError as exc:
        raise SpecValidationError(f"Invalid YAML in {path}: {exc}") from exc

    try:
        spec = GrowSpec(**data)
    except ValidationError as exc:
        raise SpecValidationError(f"Invalid GrowSpec in {path}: {exc}") from exc

    validate_spec(spec)
    return spec


def _interpolate_env_vars(text: str) -> str:
    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        value = os.environ.get(name)
        if value is None:
            raise SpecValidationError(
                f"Environment variable {name!r} referenced as "
                f"'${{{name}}}' is not set"
            )
        return value

    return _ENV_VAR_RE.sub(_replace, text)
