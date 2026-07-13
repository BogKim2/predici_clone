from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from predici_clone.core.galerkin import GalerkinField
from predici_clone.core.grid import HPMesh
from predici_clone.core.error_estimator import modal_tail_indicator


@dataclass(frozen=True)
class GalerkinProjectionResult:
    mesh: HPMesh
    coefficients: np.ndarray
    reconstructed_history: np.ndarray
    final_error_indicators: np.ndarray


def project_distribution_history(
    distribution_history: np.ndarray,
    *,
    first_length: int,
    cells: int,
    degree: int,
) -> GalerkinProjectionResult:
    values = np.asarray(distribution_history, dtype=float)
    if values.ndim != 2:
        raise ValueError("distribution_history must be a 2D array")
    if cells <= 0:
        raise ValueError("cells must be positive")
    lengths = np.arange(first_length, first_length + values.shape[0], dtype=float)
    stop = float(first_length + max(values.shape[0] - 1, 1))
    mesh = HPMesh.uniform(float(first_length), stop, cells=min(cells, max(1, values.shape[0] - 1)), degree=degree)
    reconstructed = np.empty_like(values)
    coeffs = []
    final_indicators = np.zeros(mesh.cells, dtype=float)
    for column in range(values.shape[1]):
        samples = values[:, column]

        def interpolate(x, lengths=lengths, samples=samples):
            return np.interp(x, lengths, samples, left=0.0, right=0.0)

        field = GalerkinField.project(mesh, interpolate)
        if column == values.shape[1] - 1:
            final_indicators = modal_tail_indicator(field)
        coeffs.append(field.coeffs)
        reconstructed_column = np.maximum(field.evaluate(lengths), 0.0)
        original_mass = float(np.sum(lengths * samples))
        reconstructed_mass = float(np.sum(lengths * reconstructed_column))
        if original_mass > 0 and reconstructed_mass > 0:
            reconstructed_column *= original_mass / reconstructed_mass
        reconstructed[:, column] = reconstructed_column
    return GalerkinProjectionResult(
        mesh=mesh,
        coefficients=np.column_stack(coeffs),
        reconstructed_history=reconstructed,
        final_error_indicators=final_indicators,
    )
