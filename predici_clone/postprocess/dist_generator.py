from __future__ import annotations

from collections.abc import Callable
import numpy as np


def schulz_flory(mean_length: float, nmax: int) -> np.ndarray:
    if mean_length < 1:
        raise ValueError("mean_length must be at least one")
    p = 1.0 - 1.0 / mean_length
    lengths = np.arange(1, nmax + 1)
    values = (1.0 - p) * p ** (lengths - 1)
    return values / values.sum()


def poisson_distribution(mean_length: float, nmax: int) -> np.ndarray:
    mean_events = max(mean_length - 1.0, 0.0)
    values = np.empty(nmax, dtype=float)
    values[0] = np.exp(-mean_events)
    for index in range(1, nmax):
        values[index] = values[index - 1] * mean_events / index
    return values / values.sum()


def custom_distribution(function: Callable[[np.ndarray], np.ndarray], minimum: int, maximum: int) -> np.ndarray:
    lengths = np.arange(minimum, maximum + 1)
    values = np.maximum(np.asarray(function(lengths), dtype=float), 0.0)
    if values.sum() <= 0:
        raise ValueError("custom distribution must have positive mass")
    return values / values.sum()
