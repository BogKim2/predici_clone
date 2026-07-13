from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ParticleSizeDistribution:
    diameter: np.ndarray
    number_density: np.ndarray

    @property
    def normalized(self) -> np.ndarray:
        total = float(np.sum(self.number_density))
        if total <= 0.0:
            return np.zeros_like(self.number_density, dtype=float)
        return self.number_density / total

    @property
    def d10_d50_d90(self) -> tuple[float, float, float]:
        return tuple(float(value) for value in _quantiles(self.diameter, self.normalized, (0.1, 0.5, 0.9)))

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "diameter": self.diameter,
                "number_density": self.number_density,
                "fraction": self.normalized,
            }
        )


def particle_size_from_distribution(
    chain_distribution: np.ndarray,
    *,
    first_length: int = 0,
    monomer_length: float = 0.252,
    fractal_dimension: float = 3.0,
) -> ParticleSizeDistribution:
    values = np.asarray(chain_distribution, dtype=float)
    lengths = np.arange(first_length, first_length + values.size, dtype=float)
    diameters = monomer_length * np.maximum(lengths, 1.0) ** (1.0 / max(float(fractal_dimension), 1e-12))
    return ParticleSizeDistribution(diameters, np.maximum(values, 0.0))


def _quantiles(x: np.ndarray, weights: np.ndarray, quantiles: tuple[float, ...]) -> np.ndarray:
    if x.size == 0 or np.sum(weights) <= 0:
        return np.zeros(len(quantiles), dtype=float)
    order = np.argsort(x)
    sorted_x = x[order]
    sorted_w = weights[order]
    cdf = np.cumsum(sorted_w)
    cdf = cdf / cdf[-1]
    return np.interp(np.asarray(quantiles, dtype=float), cdf, sorted_x)
