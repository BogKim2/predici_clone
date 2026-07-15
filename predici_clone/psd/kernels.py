from __future__ import annotations

from collections.abc import Callable

import numpy as np


def growth_rate(
    sizes: np.ndarray,
    concentration: float,
    saturation: float,
    *,
    rate_constant: float,
    order: float = 1.0,
    size_exponent: float = 0.0,
) -> np.ndarray:
    supersaturation = max(float(concentration) - float(saturation), 0.0)
    return rate_constant * supersaturation**order * np.asarray(sizes, dtype=float) ** size_exponent


def normalized_nucleus_shape(edges: np.ndarray, nucleus_size: float, width: float) -> np.ndarray:
    centers = 0.5 * (np.asarray(edges[:-1]) + np.asarray(edges[1:]))
    values = np.exp(-0.5 * ((centers - nucleus_size) / max(width, 1e-30)) ** 2)
    integral = float(np.sum(values * np.diff(edges)))
    return values / integral if integral > 0 else values


def nucleation_rate(
    supersaturation: float,
    *,
    primary_constant: float = 0.0,
    secondary_constant: float = 0.0,
    crystal_volume: float = 0.0,
    order: float = 1.0,
) -> float:
    driving_force = max(float(supersaturation), 0.0) ** order
    return float((primary_constant + secondary_constant * max(crystal_volume, 0.0)) * driving_force)


def constant_agglomeration_kernel(rate: float) -> Callable[[float, float], float]:
    if rate < 0:
        raise ValueError("agglomeration rate must be non-negative")
    return lambda _v, _w: float(rate)


def power_breakage_rate(rate: float, exponent: float = 0.0) -> Callable[[np.ndarray], np.ndarray]:
    return lambda sizes: float(rate) * np.asarray(sizes, dtype=float) ** float(exponent)
