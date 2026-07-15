from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ReducedDirections:
    singular_values: np.ndarray
    essential_dof: int
    condition_ratio: float
    projector: np.ndarray
    correlation: np.ndarray


def analyze_reduced_directions(jacobian: np.ndarray, condition_threshold: float = 100.0) -> ReducedDirections:
    matrix = np.asarray(jacobian, dtype=float)
    _u, singular, vt = np.linalg.svd(matrix, full_matrices=False)
    cutoff = singular[0] / condition_threshold if singular.size and condition_threshold > 0 else 0.0
    essential = int(np.sum(singular >= cutoff))
    basis = vt[:essential].T
    projector = basis @ basis.T
    covariance = np.linalg.pinv(matrix.T @ matrix)
    deviation = np.sqrt(np.maximum(np.diag(covariance), 0.0))
    correlation = np.divide(covariance, np.outer(deviation, deviation), out=np.zeros_like(covariance), where=np.outer(deviation, deviation) > 0)
    ratio = float(singular[0] / singular[-1]) if singular.size and singular[-1] > 0 else np.inf
    return ReducedDirections(singular, essential, ratio, projector, correlation)
