from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.polynomial.legendre import leggauss, legval


@dataclass(frozen=True)
class LegendreBasis:
    """Modal Legendre basis on the reference interval [-1, 1]."""

    degree: int

    def __post_init__(self) -> None:
        if self.degree < 0:
            raise ValueError("degree must be non-negative")

    @property
    def size(self) -> int:
        return self.degree + 1

    def values(self, xi: np.ndarray) -> np.ndarray:
        xi = np.asarray(xi, dtype=float)
        values = np.empty((self.size, xi.size), dtype=float)
        for j in range(self.size):
            coeffs = np.zeros(j + 1)
            coeffs[-1] = 1.0
            values[j] = legval(xi, coeffs)
        return values

    def project(self, func, order: int | None = None) -> np.ndarray:
        """Project a reference-interval function to modal coefficients."""

        quad_order = order or max(2 * self.degree + 3, 8)
        xi, weights = leggauss(quad_order)
        fvals = np.asarray(func(xi), dtype=float)
        basis_values = self.values(xi)
        coeffs = np.empty(self.size, dtype=float)
        for j in range(self.size):
            coeffs[j] = (2 * j + 1) * 0.5 * np.sum(weights * fvals * basis_values[j])
        return coeffs

    def mass_diagonal(self, width: float) -> np.ndarray:
        return width / (2 * np.arange(self.size) + 1)
