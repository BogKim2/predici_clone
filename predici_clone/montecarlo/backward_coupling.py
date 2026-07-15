from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from predici_clone.montecarlo.ensemble import ChainEnsemble


@dataclass(frozen=True)
class CouplingProfile:
    lengths: np.ndarray
    values: np.ndarray
    deterministic_mean: float

    def value_at(self, length: float) -> float:
        return float(np.interp(length, self.lengths, self.values, left=self.values[0], right=self.values[-1]))


def build_coupling_profile(
    ensemble: ChainEnsemble,
    index: str,
    *,
    deterministic_mean: float,
    relaxation: float = 1.0,
) -> CouplingProfile:
    if not 0 <= relaxation <= 1:
        raise ValueError("relaxation must be in [0, 1]")
    grouped: dict[int, list[float]] = {}
    for chain in ensemble.chains:
        grouped.setdefault(chain.length, []).append(chain.indices.get(index, 0.0))
    if not grouped:
        return CouplingProfile(np.asarray([1.0]), np.asarray([deterministic_mean]), float(deterministic_mean))
    lengths = np.asarray(sorted(grouped), dtype=float)
    sampled = np.asarray([np.mean(grouped[int(length)]) for length in lengths], dtype=float)
    sampled_mean = float(np.mean(sampled))
    centered = sampled - sampled_mean + float(deterministic_mean)
    values = (1.0 - relaxation) * float(deterministic_mean) + relaxation * centered
    return CouplingProfile(lengths, values, float(deterministic_mean))
