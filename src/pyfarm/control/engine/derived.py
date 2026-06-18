"""Derived environmental metrics computed from raw sensor readings."""

from __future__ import annotations

import math

_TETENS_A = 17.27
_TETENS_B = 237.3
_MAGNUS_A = 17.27
_MAGNUS_B = 237.7


def saturation_vapor_pressure_kpa(temp_c: float) -> float:
    denom = temp_c + _TETENS_B
    if abs(denom) < 1e-9:
        raise ValueError(f"Temperature {temp_c}°C is outside the valid range for the Tetens equation")
    return 0.6108 * math.exp(_TETENS_A * temp_c / denom)


def compute_vpd(temp_c: float, humidity_rh: float) -> float:
    """Vapour pressure deficit (kPa) from temperature (C) and RH (0-1 ratio)."""
    return saturation_vapor_pressure_kpa(temp_c) * (1 - humidity_rh)


def compute_dew_point(temp_c: float, humidity_rh: float) -> float:
    """Magnus-formula dew point (C). humidity_rh is a 0-1 ratio."""
    rh = max(humidity_rh, 1e-6)
    denom = temp_c + _MAGNUS_B
    if abs(denom) < 1e-9:
        raise ValueError(f"Temperature {temp_c}°C is outside the valid range for the Magnus formula")
    gamma = (_MAGNUS_A * temp_c) / denom + math.log(rh)
    divisor = _MAGNUS_A - gamma
    if abs(divisor) < 1e-9:
        raise ValueError(f"Dew point calculation is singular at temp={temp_c}°C, rh={humidity_rh}")
    return (_MAGNUS_B * gamma) / divisor
