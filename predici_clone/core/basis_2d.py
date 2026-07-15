from __future__ import annotations

from dataclasses import dataclass
from math import comb

import numpy as np


@dataclass(frozen=True)
class TensorDistribution2D:
    chain_lengths: np.ndarray
    compositions: np.ndarray
    density: np.ndarray

    @classmethod
    def from_outer(cls, chain_distribution: np.ndarray, composition_distribution: np.ndarray) -> "TensorDistribution2D":
        chain = np.asarray(chain_distribution, dtype=float)
        composition = np.asarray(composition_distribution, dtype=float)
        if chain.ndim != 1 or composition.ndim != 1:
            raise ValueError("chain and composition distributions must be one-dimensional")
        if np.any(chain < 0.0) or np.any(composition < 0.0):
            raise ValueError("distributions must be non-negative")
        chain_total = float(np.sum(chain))
        composition_total = float(np.sum(composition))
        if chain_total <= 0.0 or composition_total <= 0.0:
            raise ValueError("distributions must have positive mass")
        density = np.outer(chain / chain_total, composition / composition_total)
        return cls(
            chain_lengths=np.arange(1, chain.size + 1, dtype=float),
            compositions=np.linspace(0.0, 1.0, composition.size),
            density=density,
        )

    def chain_marginal(self) -> np.ndarray:
        return np.sum(self.density, axis=1)

    def composition_marginal(self) -> np.ndarray:
        return np.sum(self.density, axis=0)

    def mean_composition(self) -> float:
        return float(np.sum(self.composition_marginal() * self.compositions))


def flory_chain_distribution(probability: float, nmax: int) -> np.ndarray:
    if not 0.0 <= probability < 1.0:
        raise ValueError("probability must be in [0, 1)")
    lengths = np.arange(1, int(nmax) + 1, dtype=float)
    distribution = (1.0 - probability) * probability ** (lengths - 1.0)
    total = float(np.sum(distribution))
    return distribution / total if total > 0.0 else distribution


def binomial_composition_distribution(monomer_fraction: float, bins: int) -> np.ndarray:
    if bins < 2:
        raise ValueError("bins must be at least 2")
    p = float(np.clip(monomer_fraction, 0.0, 1.0))
    degree = int(bins) - 1
    values = []
    for k in range(degree + 1):
        coefficient = float(comb(degree, k))
        values.append(coefficient * p**k * (1.0 - p) ** (degree - k))
    distribution = np.asarray(values, dtype=float)
    return distribution / float(np.sum(distribution))
