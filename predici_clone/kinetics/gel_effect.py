from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class GelEffectRates:
    conversion: float
    relative_viscosity: float
    kp: float
    kt: float


def apply_gel_effect(
    conversion: float,
    *,
    kp0: float,
    kt0: float,
    viscosity: Callable[[float], float],
    kp_modifier: Callable[[float, float], float] | None = None,
    kt_modifier: Callable[[float, float], float] | None = None,
) -> GelEffectRates:
    x = min(max(float(conversion), 0.0), 1.0)
    eta = max(float(viscosity(x)), 1e-30)
    kp = kp_modifier(x, eta) if kp_modifier else kp0 / eta**0.1
    kt = kt_modifier(x, eta) if kt_modifier else kt0 / eta
    return GelEffectRates(x, eta, float(kp), float(kt))
