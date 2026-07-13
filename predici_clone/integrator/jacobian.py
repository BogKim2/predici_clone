from __future__ import annotations

import numpy as np
from scipy.sparse import csc_matrix


def finite_difference_jacobian(rhs, t: float, y: np.ndarray, eps: float = 1e-7) -> csc_matrix:
    y = np.asarray(y, dtype=float)
    base = rhs(t, y)
    jac = np.empty((y.size, y.size), dtype=float)
    for j in range(y.size):
        perturbed = y.copy()
        step = eps * max(1.0, abs(y[j]))
        perturbed[j] += step
        jac[:, j] = (rhs(t, perturbed) - base) / step
    return csc_matrix(jac)
