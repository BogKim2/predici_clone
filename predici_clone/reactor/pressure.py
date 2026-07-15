from __future__ import annotations

from collections.abc import Callable

import numpy as np


def pressure_at(time: float, *, table: tuple[tuple[float, float], ...] = (), script: Callable[[float], float] | None = None, default: float = 101325.0) -> float:
    if script is not None:
        value = float(script(float(time)))
    elif table:
        points = np.asarray(table, dtype=float)
        value = float(np.interp(time, points[:, 0], points[:, 1]))
    else:
        value = float(default)
    if value <= 0:
        raise ValueError("pressure must be positive")
    return value


def pressure_arrhenius_factor(pressure: float, reference_pressure: float, activation_volume_over_r: float, temperature: float) -> float:
    return float(np.exp(-activation_volume_over_r * (pressure - reference_pressure) / temperature))
