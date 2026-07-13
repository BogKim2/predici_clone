from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.polynomial.legendre import leggauss

from predici_clone.core.basis import LegendreBasis
from predici_clone.core.grid import HPMesh


@dataclass
class GalerkinField:
    """Piecewise Legendre approximation of a chain-length distribution."""

    mesh: HPMesh
    coeffs: np.ndarray

    @classmethod
    def project(cls, mesh: HPMesh, func) -> "GalerkinField":
        coeffs = np.empty(mesh.dofs, dtype=float)
        offsets = mesh.offsets
        for cell, degree in enumerate(mesh.degrees):
            left, right = mesh.cell_bounds(cell)
            basis = LegendreBasis(degree)

            def reference_func(xi, left=left, right=right):
                x = 0.5 * (right - left) * xi + 0.5 * (left + right)
                return func(x)

            coeffs[offsets[cell] : offsets[cell + 1]] = basis.project(reference_func)
        return cls(mesh, coeffs)

    def __post_init__(self) -> None:
        coeffs = np.asarray(self.coeffs, dtype=float)
        if coeffs.shape != (self.mesh.dofs,):
            raise ValueError("coefficient vector length does not match mesh")
        self.coeffs = coeffs

    def evaluate(self, x: np.ndarray) -> np.ndarray:
        x = np.asarray(x, dtype=float)
        values = np.zeros_like(x, dtype=float)
        offsets = self.mesh.offsets
        for cell, degree in enumerate(self.mesh.degrees):
            left, right = self.mesh.cell_bounds(cell)
            mask = (x >= left) & (x <= right if cell == self.mesh.cells - 1 else x < right)
            if not np.any(mask):
                continue
            xi = (2 * x[mask] - left - right) / (right - left)
            basis_values = LegendreBasis(degree).values(xi)
            cell_coeffs = self.coeffs[offsets[cell] : offsets[cell + 1]]
            values[mask] = cell_coeffs @ basis_values
        return values

    def moment(self, order: int, quadrature_order: int = 16) -> float:
        xi, weights = leggauss(quadrature_order)
        total = 0.0
        offsets = self.mesh.offsets
        for cell, degree in enumerate(self.mesh.degrees):
            left, right = self.mesh.cell_bounds(cell)
            width = right - left
            x = 0.5 * width * xi + 0.5 * (left + right)
            basis_values = LegendreBasis(degree).values(xi)
            cell_coeffs = self.coeffs[offsets[cell] : offsets[cell + 1]]
            total += 0.5 * width * np.sum(weights * (x**order) * (cell_coeffs @ basis_values))
        return float(total)

    def h_refined(self, marked_cells: set[int]) -> "GalerkinField":
        new_mesh = self.mesh.refine_h(marked_cells)
        return GalerkinField.project(new_mesh, self.evaluate)

    def p_refined(self, marked_cells: set[int], amount: int = 1) -> "GalerkinField":
        new_mesh = self.mesh.refine_p(marked_cells, amount)
        return GalerkinField.project(new_mesh, self.evaluate)
