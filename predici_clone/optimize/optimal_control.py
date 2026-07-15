from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from scipy.optimize import differential_evolution


@dataclass(frozen=True)
class ControlResult:
    controls: np.ndarray
    objective: float
    success: bool


def optimize_control(objective: Callable[[np.ndarray], float], bounds: tuple[tuple[float, float], ...], *, safety: Callable[[np.ndarray], bool] | None = None, seed: int = 1, maxiter: int = 30) -> ControlResult:
    def constrained(values: np.ndarray) -> float:
        return float(objective(values)) if safety is None or safety(values) else 1e30
    result = differential_evolution(constrained, bounds, seed=seed, maxiter=maxiter, polish=True)
    return ControlResult(np.asarray(result.x), float(result.fun), bool(result.success or np.isfinite(result.fun)))
