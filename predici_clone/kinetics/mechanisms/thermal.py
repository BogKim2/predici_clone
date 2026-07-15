from __future__ import annotations

import numpy as np
from collections.abc import Callable


R = 8.314462618


def thermal_initiation_rate(monomer_concentration: float, temperature: float, *, pre_exponential: float, activation_energy: float, order: float = 3.0) -> float:
    if temperature <= 0 or monomer_concentration < 0:
        raise ValueError("temperature must be positive and concentration non-negative")
    return float(pre_exponential * np.exp(-activation_energy / (R * temperature)) * monomer_concentration**order)


def change_characteristic(value: float, conversion: float, modifier: Callable[[float, float], float]) -> float:
    return float(modifier(float(value), float(conversion)))
