from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from scipy.optimize import minimize


@dataclass(frozen=True)
class RobustResult:
    parameters: np.ndarray
    nominal_objective: float
    robust_objective: float
    success: bool


def sigma_points(mean: np.ndarray, covariance: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    center = np.asarray(mean, dtype=float)
    matrix = np.asarray(covariance, dtype=float)
    if matrix.shape != (center.size, center.size):
        raise ValueError("covariance shape must match mean")
    root = np.linalg.cholesky(matrix + np.eye(center.size) * 1e-15)
    scale = np.sqrt(center.size)
    points = [center]
    for column in root.T:
        points.extend((center + scale * column, center - scale * column))
    weights = np.asarray([0.0] + [1.0 / (2 * center.size)] * (2 * center.size))
    return np.asarray(points), weights


def robust_optimize(
    objective: Callable[[np.ndarray], float],
    initial: np.ndarray,
    covariance: np.ndarray,
    bounds: tuple[tuple[float, float], ...],
    *,
    uncertainty_weight: float = 1.0,
) -> RobustResult:
    points, weights = sigma_points(np.zeros(len(initial)), covariance)

    def robust(values: np.ndarray) -> float:
        samples = np.asarray([objective(values + offset) for offset in points], dtype=float)
        mean = float(weights @ samples)
        return mean + uncertainty_weight * float(np.sqrt(weights @ (samples - mean) ** 2))

    result = minimize(robust, np.asarray(initial, dtype=float), bounds=bounds, method="L-BFGS-B")
    return RobustResult(np.asarray(result.x), float(objective(result.x)), float(result.fun), bool(result.success))


def parity_data(measured: np.ndarray, predicted: np.ndarray, *, relative_cutoff: float = 0.0) -> dict[str, np.ndarray | float]:
    observed = np.asarray(measured, dtype=float)
    modeled = np.asarray(predicted, dtype=float)
    mask = np.isfinite(observed) & np.isfinite(modeled) & (np.abs(observed) >= relative_cutoff)
    residual = modeled[mask] - observed[mask]
    relative = np.divide(residual, observed[mask], out=np.zeros_like(residual), where=observed[mask] != 0)
    return {"measured": observed[mask], "predicted": modeled[mask], "residual": residual, "f2": float(np.sum(relative**2))}
