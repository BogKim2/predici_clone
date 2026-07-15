from __future__ import annotations

from collections.abc import Callable

import numpy as np


def internal_numerical_jacobian(function: Callable[[np.ndarray], np.ndarray], parameters: np.ndarray, relative_step: float | None = None) -> np.ndarray:
    values = np.asarray(parameters, dtype=float)
    base = np.asarray(function(values), dtype=float)
    step_scale = np.sqrt(np.finfo(float).eps) if relative_step is None else float(relative_step)
    jacobian = np.empty((base.size, values.size))
    for index, value in enumerate(values):
        step = step_scale * max(abs(value), 1.0)
        perturbed = values.copy()
        perturbed[index] += step
        jacobian[:, index] = (np.asarray(function(perturbed), dtype=float) - base) / step
    return jacobian
