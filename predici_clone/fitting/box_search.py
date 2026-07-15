from __future__ import annotations

from collections.abc import Callable
from itertools import product

import numpy as np


def box_search(objective: Callable[[np.ndarray], float], bounds: tuple[tuple[float, float], ...], points: int | tuple[int, ...], *, logarithmic: tuple[bool, ...] | None = None) -> tuple[np.ndarray, float]:
    counts = (points,) * len(bounds) if isinstance(points, int) else points
    log_flags = logarithmic or (False,) * len(bounds)
    axes = [np.geomspace(lower, upper, count) if use_log else np.linspace(lower, upper, count) for (lower, upper), count, use_log in zip(bounds, counts, log_flags)]
    candidates = (np.asarray(values) for values in product(*axes))
    best = min(((candidate, float(objective(candidate))) for candidate in candidates), key=lambda item: item[1])
    return best
