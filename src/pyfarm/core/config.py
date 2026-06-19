"""Configuration, environment profiles and secret resolution.

Two concerns live here, shared by the spec loader, the CLI and notification
channels:

* ``${VAR}`` interpolation — substitute environment variables into spec values
  (and any other strings), so secrets like API tokens are never committed to a
  GrowSpec. This is the single implementation the spec loader delegates to.
* environment profiles — load a named ``.env``-style file of ``KEY=value`` lines
  (e.g. a per-chamber or per-deployment profile) into the process environment so
  the same spec can be pointed at different secrets/credentials.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any, Mapping

_ENV_VAR_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class MissingEnvVar(KeyError):
    """Raised when a ``${VAR}`` reference has no value in the environment."""

    def __init__(self, name: str) -> None:
        self.name = name
        super().__init__(name)

    def __str__(self) -> str:
        return (
            f"Environment variable {self.name!r} referenced as "
            f"'${{{self.name}}}' is not set"
        )


def interpolate_env_vars(value: Any, *, env: Mapping[str, str] | None = None) -> Any:
    """Recursively substitute ``${VAR}`` references in ``value``.

    Walks dicts and lists; replaces references in strings. Raises
    :class:`MissingEnvVar` if a referenced variable is absent from ``env``
    (defaults to ``os.environ``).
    """
    environ = os.environ if env is None else env
    if isinstance(value, str):
        def _replace(match: re.Match[str]) -> str:
            name = match.group(1)
            if name not in environ:
                raise MissingEnvVar(name)
            return environ[name]

        return _ENV_VAR_RE.sub(_replace, value)
    if isinstance(value, dict):
        return {k: interpolate_env_vars(v, env=env) for k, v in value.items()}
    if isinstance(value, list):
        return [interpolate_env_vars(item, env=env) for item in value]
    return value


def parse_env_file(text: str) -> dict[str, str]:
    """Parse ``.env``-style ``KEY=value`` content.

    Blank lines and ``#`` comments are ignored; surrounding quotes on values are
    stripped; a leading ``export`` keyword is tolerated.
    """
    result: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("export "):
            stripped = stripped[len("export ") :]
        if "=" not in stripped:
            continue
        key, _, raw = stripped.partition("=")
        key = key.strip()
        val = raw.strip()
        if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
            val = val[1:-1]
        result[key] = val
    return result


def load_profile(
    name: str | None,
    *,
    profiles_dir: str | Path | None = None,
    override: bool = False,
) -> dict[str, str]:
    """Load a named environment profile into ``os.environ``.

    Looks for ``<profiles_dir>/<name>.env`` (``profiles_dir`` defaults to the
    ``PYFARM_PROFILES_DIR`` env var, or ``./profiles``). Existing variables are
    preserved unless ``override`` is set. Returns the variables that were
    loaded. A ``None`` or empty ``name`` is a no-op (returns ``{}``).
    """
    if not name:
        return {}
    base = Path(
        profiles_dir
        or os.environ.get("PYFARM_PROFILES_DIR")
        or "profiles"
    )
    path = base / f"{name}.env"
    if not path.exists():
        raise FileNotFoundError(f"Profile {name!r} not found at {path}")
    loaded = parse_env_file(path.read_text())
    for key, val in loaded.items():
        if override or key not in os.environ:
            os.environ[key] = val
    return loaded
