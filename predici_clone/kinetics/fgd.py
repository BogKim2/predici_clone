from __future__ import annotations

from collections import Counter
from math import comb

import numpy as np

from predici_clone.montecarlo.ensemble import ChainEnsemble


def counter_subdistribution(functionality: int, reacted_fraction: float) -> dict[str, float]:
    if functionality < 0:
        raise ValueError("functionality must be non-negative")
    p = float(np.clip(reacted_fraction, 0.0, 1.0))
    exact = {count: comb(functionality, count) * p**count * (1.0 - p) ** (functionality - count) for count in range(functionality + 1)}
    return {
        "0": exact.get(0, 0.0),
        "1": exact.get(1, 0.0),
        "2": exact.get(2, 0.0),
        "3+": sum(value for count, value in exact.items() if count >= 3),
    }


def ensemble_subdistribution(ensemble: ChainEnsemble, index: str = "functional_groups") -> dict[str, float]:
    counts = Counter(int(round(chain.indices.get(index, 0.0))) for chain in ensemble.chains)
    total = max(len(ensemble.chains), 1)
    return {
        "0": counts[0] / total,
        "1": counts[1] / total,
        "2": counts[2] / total,
        "3+": sum(value for key, value in counts.items() if key >= 3) / total,
    }
