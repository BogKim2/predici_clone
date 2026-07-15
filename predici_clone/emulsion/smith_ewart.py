from __future__ import annotations

import numpy as np


def smith_ewart_steady_state(
    *,
    entry_rate: float,
    exit_rate: float,
    termination_rate: float = 0.0,
    nmax: int = 20,
) -> np.ndarray:
    if entry_rate < 0 or exit_rate < 0 or termination_rate < 0 or nmax < 1:
        raise ValueError("rates must be non-negative and nmax must be positive")
    generator = np.zeros((nmax + 1, nmax + 1), dtype=float)
    for radicals in range(nmax + 1):
        transitions: list[tuple[int, float]] = []
        if radicals < nmax:
            transitions.append((radicals + 1, entry_rate))
        if radicals > 0:
            transitions.append((radicals - 1, exit_rate * radicals))
        if radicals > 1:
            transitions.append((radicals - 2, termination_rate * radicals * (radicals - 1) / 2.0))
        for target, rate in transitions:
            generator[target, radicals] += rate
            generator[radicals, radicals] -= rate
    system = generator.copy()
    system[-1, :] = 1.0
    rhs = np.zeros(nmax + 1)
    rhs[-1] = 1.0
    distribution = np.linalg.lstsq(system, rhs, rcond=None)[0]
    distribution = np.maximum(distribution, 0.0)
    return distribution / distribution.sum()


def radical_moments(distribution: np.ndarray, highest_order: int = 2) -> tuple[float, ...]:
    values = np.maximum(np.asarray(distribution, dtype=float), 0.0)
    radicals = np.arange(values.size, dtype=float)
    return tuple(float(np.sum(radicals**order * values)) for order in range(highest_order + 1))


def shifted_first_moment(distribution: np.ndarray) -> float:
    moment_zero, moment_one = radical_moments(distribution, 1)
    return moment_one - moment_zero
