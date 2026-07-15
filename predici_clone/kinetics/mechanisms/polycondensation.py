from __future__ import annotations

from dataclasses import dataclass
from math import comb

import numpy as np


@dataclass(frozen=True)
class EndGroupPopulation:
    a: float
    b: float
    c: float = 0.0
    d: float = 0.0

    def selective_rate(self, rate_constants: dict[str, float]) -> float:
        return float(
            rate_constants.get("AB", 0.0) * self.a * self.b
            + rate_constants.get("AC", 0.0) * self.a * self.c
            + rate_constants.get("AD", 0.0) * self.a * self.d
        )


def stoichiometric_factorial(available_groups: int, selected_groups: int) -> int:
    if available_groups < 0 or selected_groups < 0 or selected_groups > available_groups:
        return 0
    return comb(available_groups, selected_groups)


def schulz_flory_distribution(conversion: float, nmax: int) -> np.ndarray:
    if nmax < 1:
        raise ValueError("nmax must be positive")
    p = float(np.clip(conversion, 0.0, 1.0 - 1e-12))
    degree = np.arange(1, nmax + 1, dtype=float)
    values = (1.0 - p) * p ** (degree - 1.0)
    return values / values.sum()


def carothers_moments(conversion: float) -> tuple[float, float, float]:
    p = float(np.clip(conversion, 0.0, 1.0 - 1e-12))
    number_average = 1.0 / (1.0 - p)
    weight_average = (1.0 + p) / (1.0 - p)
    return number_average, weight_average, 1.0 + p
