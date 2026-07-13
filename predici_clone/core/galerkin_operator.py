from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from predici_clone.core.galerkin import GalerkinField
from predici_clone.core.grid import HPMesh
from predici_clone.kinetics.rate_terms import branching, chain_transfer, polymer_partition, scission, termination_combination


@dataclass(frozen=True)
class GalerkinOperators:
    propagation: np.ndarray
    loss: np.ndarray
    source: np.ndarray


class GalerkinOperatorAssembler:
    """Assemble simple linear operators in modal Galerkin coefficient space.

    Propagation uses the chain-length shift form `c(n-1) - c(n)`, projected back
    onto the active h-p mesh. This is a first direct coefficient-space operator
    for the FRP propagation term; nonlinear species-dependent rates remain in
    the caller.
    """

    def __init__(self, mesh: HPMesh, *, shift: float = 1.0) -> None:
        self.mesh = mesh
        self.shift = shift

    def assemble(self) -> GalerkinOperators:
        propagation = np.empty((self.mesh.dofs, self.mesh.dofs), dtype=float)
        for column in range(self.mesh.dofs):
            basis_coeffs = np.zeros(self.mesh.dofs, dtype=float)
            basis_coeffs[column] = 1.0
            basis_field = GalerkinField(self.mesh, basis_coeffs)

            def shifted_difference(x, basis_field=basis_field):
                x = np.asarray(x, dtype=float)
                shifted = basis_field.evaluate(x - self.shift)
                current = basis_field.evaluate(x)
                return shifted - current

            propagation[:, column] = GalerkinField.project(self.mesh, shifted_difference).coeffs
        loss = -np.eye(self.mesh.dofs)
        source = self._source_vector()
        return GalerkinOperators(propagation=propagation, loss=loss, source=source)

    def rhs(
        self,
        coeffs: np.ndarray,
        *,
        propagation_rate: float,
        loss_rate: float = 0.0,
        source_rate: float = 0.0,
    ) -> np.ndarray:
        operators = self.assemble()
        return (
            propagation_rate * operators.propagation @ coeffs
            + loss_rate * operators.loss @ coeffs
            + source_rate * operators.source
        )

    def termination_combination_rhs(self, coeffs: np.ndarray, *, rate: float) -> np.ndarray:
        return self._project_discrete_reaction(coeffs, lambda values: termination_combination(values, rate))

    def chain_transfer_rhs(self, coeffs: np.ndarray, *, rate: float, target_length: int = 0) -> np.ndarray:
        return self._project_discrete_reaction(coeffs, lambda values: chain_transfer(values, rate, target_length=target_length))

    def scission_rhs(self, coeffs: np.ndarray, *, rate: float) -> np.ndarray:
        return self._project_discrete_reaction(coeffs, lambda values: scission(values, rate))

    def branching_rhs(self, coeffs: np.ndarray, *, rate: float, branch_factor: float = 2.0) -> np.ndarray:
        return self._project_discrete_reaction(coeffs, lambda values: branching(values, rate, branch_factor=branch_factor))

    def polymer_partition_rhs(self, coeffs: np.ndarray, *, rate: float, cutoff: int | None = None) -> np.ndarray:
        return self._project_discrete_reaction(coeffs, lambda values: polymer_partition(values, rate, cutoff=cutoff))

    def nonlinear_rhs(
        self,
        coeffs: np.ndarray,
        *,
        termination_combination_rate: float = 0.0,
        chain_transfer_rate: float = 0.0,
        scission_rate: float = 0.0,
        branching_rate: float = 0.0,
        polymer_partition_rate: float = 0.0,
        transfer_target_length: int = 0,
    ) -> np.ndarray:
        total = np.zeros(self.mesh.dofs, dtype=float)
        if termination_combination_rate:
            total += self.termination_combination_rhs(coeffs, rate=termination_combination_rate)
        if chain_transfer_rate:
            total += self.chain_transfer_rhs(coeffs, rate=chain_transfer_rate, target_length=transfer_target_length)
        if scission_rate:
            total += self.scission_rhs(coeffs, rate=scission_rate)
        if branching_rate:
            total += self.branching_rhs(coeffs, rate=branching_rate)
        if polymer_partition_rate:
            total += self.polymer_partition_rhs(coeffs, rate=polymer_partition_rate)
        return total

    def _source_vector(self) -> np.ndarray:
        left, right = self.mesh.cell_bounds(0)
        width = right - left

        def source(x):
            x = np.asarray(x, dtype=float)
            return np.where((x >= left) & (x <= right), 1.0 / width, 0.0)

        return GalerkinField.project(self.mesh, source).coeffs

    def _chain_grid(self) -> np.ndarray:
        start = int(np.floor(self.mesh.edges[0]))
        stop = int(np.ceil(self.mesh.edges[-1]))
        return np.arange(start, stop + 1, dtype=float)

    def _project_discrete_reaction(self, coeffs: np.ndarray, reaction) -> np.ndarray:
        field = GalerkinField(self.mesh, coeffs)
        lengths = self._chain_grid()
        values = np.maximum(field.evaluate(lengths), 0.0)
        rhs_values = np.asarray(reaction(values), dtype=float)

        def rhs_func(x):
            x = np.asarray(x, dtype=float)
            return np.interp(x, lengths, rhs_values, left=rhs_values[0], right=rhs_values[-1])

        return GalerkinField.project(self.mesh, rhs_func).coeffs
