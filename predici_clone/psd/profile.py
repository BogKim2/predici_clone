from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PSDProfile:
    edges: np.ndarray
    number_density: np.ndarray
    shape_factor: float = np.pi / 6.0

    def __post_init__(self) -> None:
        edges = np.asarray(self.edges, dtype=float)
        density = np.asarray(self.number_density, dtype=float)
        if edges.ndim != 1 or density.ndim != 1 or edges.size != density.size + 1:
            raise ValueError("edges must contain one more value than number_density")
        if np.any(np.diff(edges) <= 0) or np.any(density < 0):
            raise ValueError("profile grid must increase and density must be non-negative")
        object.__setattr__(self, "edges", edges)
        object.__setattr__(self, "number_density", density)

    @classmethod
    def linear(cls, minimum: float, maximum: float, bins: int, density: float = 0.0) -> PSDProfile:
        return cls(np.linspace(minimum, maximum, bins + 1), np.full(bins, density, dtype=float))

    @classmethod
    def logarithmic(cls, minimum: float, maximum: float, bins: int, density: float = 0.0) -> PSDProfile:
        if minimum <= 0:
            raise ValueError("logarithmic grid minimum must be positive")
        return cls(np.geomspace(minimum, maximum, bins + 1), np.full(bins, density, dtype=float))

    @property
    def centers(self) -> np.ndarray:
        return 0.5 * (self.edges[:-1] + self.edges[1:])

    @property
    def widths(self) -> np.ndarray:
        return np.diff(self.edges)

    @property
    def volume_density(self) -> np.ndarray:
        return self.shape_factor * self.centers**3 * self.number_density

    def moment(self, order: int) -> float:
        if order < 0:
            raise ValueError("moment order must be non-negative")
        return float(np.sum(self.centers**order * self.number_density * self.widths))

    @property
    def mean_size(self) -> float:
        return self.moment(1) / max(self.moment(0), 1e-30)

    @property
    def total_volume(self) -> float:
        return self.shape_factor * self.moment(3)

    def with_density(self, number_density: np.ndarray) -> PSDProfile:
        return PSDProfile(self.edges.copy(), np.maximum(np.asarray(number_density, dtype=float), 0.0), self.shape_factor)

    def expanded(self, factor: float = 2.0, bins: int | None = None) -> PSDProfile:
        if factor <= 1:
            raise ValueError("expansion factor must exceed one")
        additional = int(bins or max(1, self.number_density.size // 2))
        spacing = self.widths[-1]
        extra_edges = self.edges[-1] + spacing * np.arange(1, additional + 1)
        if extra_edges[-1] < self.edges[-1] * factor:
            extra_edges = np.linspace(self.edges[-1], self.edges[-1] * factor, additional + 1)[1:]
        return PSDProfile(
            np.concatenate((self.edges, extra_edges)),
            np.concatenate((self.number_density, np.zeros(additional))),
            self.shape_factor,
        )
