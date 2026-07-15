from __future__ import annotations

from dataclasses import dataclass

import numpy as np


R = 8.314462618


@dataclass(frozen=True)
class ArrheniusFit:
    pre_exponential: float
    activation_energy: float
    r_squared: float


def fit_arrhenius(temperature: np.ndarray, rate: np.ndarray, reference_temperature: float | None = None) -> ArrheniusFit:
    t = np.asarray(temperature, dtype=float)
    k = np.asarray(rate, dtype=float)
    if np.any(t <= 0) or np.any(k <= 0):
        raise ValueError("temperature and rate must be positive")
    x = 1.0 / t if reference_temperature is None else 1.0 / t - 1.0 / reference_temperature
    slope, intercept = np.polyfit(x, np.log(k), 1)
    predicted = slope * x + intercept
    ss_res = float(np.sum((np.log(k) - predicted) ** 2))
    ss_tot = float(np.sum((np.log(k) - np.mean(np.log(k))) ** 2))
    return ArrheniusFit(float(np.exp(intercept)), float(-slope * R), 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0)
