from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from predici_clone.psd.profile import PSDProfile


@dataclass(frozen=True)
class PSDData:
    size: np.ndarray
    value: np.ndarray
    basis: str = "number"
    scale: float = 1.0
    relative: bool = False

    def normalized(self) -> PSDData:
        values = np.maximum(np.asarray(self.value, dtype=float), 0.0)
        total = float(values.sum())
        return PSDData(np.asarray(self.size, dtype=float), values / total if total > 0 else values, self.basis, self.scale, True)


def generated_profile(
    edges: np.ndarray,
    *,
    distribution: str,
    location: float,
    scale: float,
    total_number: float = 1.0,
) -> PSDProfile:
    grid = np.asarray(edges, dtype=float)
    centers = 0.5 * (grid[:-1] + grid[1:])
    if distribution == "gaussian":
        density = np.exp(-0.5 * ((centers - location) / scale) ** 2)
    elif distribution == "lognormal":
        density = np.exp(-0.5 * ((np.log(np.maximum(centers, 1e-30)) - location) / scale) ** 2) / np.maximum(centers, 1e-30)
    elif distribution == "uniform":
        density = np.where(np.abs(centers - location) <= scale, 1.0, 0.0)
    else:
        raise ValueError(f"Unsupported PSD distribution: {distribution}")
    integral = float(np.sum(density * np.diff(grid)))
    return PSDProfile(grid, density * total_number / integral if integral > 0 else density)
