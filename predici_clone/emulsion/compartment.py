from __future__ import annotations

import numpy as np


def compartmentalization_factor(distribution: np.ndarray) -> float:
    values = np.maximum(np.asarray(distribution, dtype=float), 0.0)
    total = float(values.sum())
    if total <= 0:
        return 0.0
    radicals = np.arange(values.size, dtype=float)
    mean = float(np.sum(radicals * values) / total)
    factorial_second = float(np.sum(radicals * (radicals - 1.0) * values) / total)
    return factorial_second / mean**2 if mean > 0 else 0.0


def compartment_termination_rate(pseudo_bulk_rate: float, distribution: np.ndarray) -> float:
    return float(pseudo_bulk_rate) * compartmentalization_factor(distribution)
