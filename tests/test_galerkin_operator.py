import numpy as np

from predici_clone.core.galerkin import GalerkinField
from predici_clone.core.galerkin_operator import GalerkinOperatorAssembler
from predici_clone.core.grid import HPMesh
from predici_clone.engine.galerkin_system import GalerkinFRPBatchSystem, GalerkinPBESystem
from predici_clone.kinetics import FRPScheme, SpeciesState


def test_galerkin_operator_shapes_and_loss_identity():
    mesh = HPMesh.uniform(0.0, 6.0, cells=3, degree=2)
    operators = GalerkinOperatorAssembler(mesh).assemble()

    assert operators.propagation.shape == (mesh.dofs, mesh.dofs)
    assert operators.loss.shape == (mesh.dofs, mesh.dofs)
    assert operators.source.shape == (mesh.dofs,)
    np.testing.assert_allclose(operators.loss, -np.eye(mesh.dofs))


def test_galerkin_propagation_rhs_moves_mass_to_larger_chain_lengths():
    mesh = HPMesh.uniform(0.0, 8.0, cells=4, degree=2)
    field = GalerkinField.project(mesh, lambda x: np.exp(-2.0 * x))
    assembler = GalerkinOperatorAssembler(mesh)
    rhs = assembler.rhs(field.coeffs, propagation_rate=0.5)
    derivative = GalerkinField(mesh, rhs)

    assert derivative.moment(1) > 0.0


def test_galerkin_source_vector_has_unit_integral():
    mesh = HPMesh.uniform(0.0, 4.0, cells=2, degree=1)
    source = GalerkinField(mesh, GalerkinOperatorAssembler(mesh).assemble().source)

    np.testing.assert_allclose(source.moment(0), 1.0, atol=1e-12)


def test_galerkin_nonlinear_reaction_rhs_projects_transfer_scission_and_combination():
    mesh = HPMesh.uniform(0.0, 8.0, cells=4, degree=2)
    field = GalerkinField.project(mesh, lambda x: np.exp(-0.5 * (x - 5.0) ** 2))
    assembler = GalerkinOperatorAssembler(mesh)

    transfer = GalerkinField(mesh, assembler.chain_transfer_rhs(field.coeffs, rate=0.2))
    scission = GalerkinField(mesh, assembler.scission_rhs(field.coeffs, rate=0.2))
    combination = assembler.termination_combination_rhs(field.coeffs, rate=0.05)
    combined = assembler.nonlinear_rhs(
        field.coeffs,
        termination_combination_rate=0.05,
        chain_transfer_rate=0.2,
        scission_rate=0.1,
    )

    assert transfer.moment(1) < 0.0
    assert scission.moment(0) > 0.0
    assert combination.shape == (mesh.dofs,)
    assert np.linalg.norm(combined) > 0.0


def test_galerkin_nonlinear_reaction_rhs_projects_branching_and_partition():
    mesh = HPMesh.uniform(0.0, 8.0, cells=4, degree=2)
    field = GalerkinField.project(mesh, lambda x: np.exp(-0.5 * (x - 2.0) ** 2))
    assembler = GalerkinOperatorAssembler(mesh)

    branching_rhs = assembler.branching_rhs(field.coeffs, rate=0.2)
    partition_rhs = assembler.polymer_partition_rhs(field.coeffs, rate=0.1)
    combined = assembler.nonlinear_rhs(field.coeffs, branching_rate=0.2, polymer_partition_rate=0.1)

    assert branching_rhs.shape == (mesh.dofs,)
    assert partition_rhs.shape == (mesh.dofs,)
    assert np.linalg.norm(combined) > 0.0


def test_galerkin_pbe_system_integrates_coefficients():
    mesh = HPMesh.uniform(0.0, 8.0, cells=4, degree=2)
    initial = GalerkinField.project(mesh, lambda x: np.exp(-x))
    system = GalerkinPBESystem(mesh=mesh, initial_field=initial, propagation_rate=0.2, loss_rate=0.01)

    result = system.solve((0.0, 1.0), t_eval=np.linspace(0.0, 1.0, 4))
    final = GalerkinField(mesh, result.y[:, -1])

    assert result.success
    assert result.y.shape == (mesh.dofs, 4)
    assert final.moment(1) > initial.moment(1)


def test_galerkin_pbe_system_integrates_nonlinear_rates():
    mesh = HPMesh.uniform(0.0, 8.0, cells=4, degree=2)
    initial = GalerkinField.project(mesh, lambda x: np.exp(-0.8 * x))
    system = GalerkinPBESystem(
        mesh=mesh,
        initial_field=initial,
        propagation_rate=0.0,
        chain_transfer_rate=0.2,
        scission_rate=0.05,
    )

    result = system.solve((0.0, 0.5), t_eval=np.linspace(0.0, 0.5, 3))
    final = GalerkinField(mesh, result.y[:, -1])

    assert result.success
    assert final.moment(1) < initial.moment(1)


def test_galerkin_frp_batch_system_couples_species_and_coefficients():
    mesh = HPMesh.uniform(0.0, 12.0, cells=4, degree=2)
    initial = GalerkinField.project(mesh, lambda x: np.zeros_like(np.asarray(x, dtype=float)))
    system = GalerkinFRPBatchSystem(
        mesh=mesh,
        initial_field=initial,
        species=SpeciesState(monomer=2.0, initiator=0.1, radicals=0.01),
        scheme=FRPScheme(kp=0.08, kt=0.05, kd=0.02, initiator_efficiency=0.6),
    )

    result = system.solve((0.0, 1.0), t_eval=np.linspace(0.0, 1.0, 4))
    final = GalerkinField(mesh, result.y[3:, -1])

    assert result.success
    assert result.y.shape == (mesh.dofs + 3, 4)
    assert result.y[0, -1] < result.y[0, 0]
    assert result.y[1, -1] < result.y[1, 0]
    assert final.moment(0) > 0.0
