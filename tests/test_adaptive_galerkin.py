import numpy as np

from predici_clone.core.adaptive import adapt_galerkin_field
from predici_clone.core.galerkin import GalerkinField
from predici_clone.core.grid import HPMesh


def test_adaptive_galerkin_field_refines_marked_cells_and_remaps_coefficients():
    mesh = HPMesh.uniform(0.0, 4.0, cells=2, degree=1)
    field = GalerkinField.project(mesh, lambda x: np.exp(-x) + 0.2 * np.sin(4.0 * x))
    original_mass = field.moment(0)

    adapted = adapt_galerkin_field(field, tolerance=0.01, strategy="mixed", max_degree=3)

    assert adapted.changed
    assert adapted.field.mesh.dofs > field.mesh.dofs
    assert adapted.h_marked or adapted.p_marked
    np.testing.assert_allclose(adapted.field.moment(0), original_mass, rtol=2e-2)


def test_adaptive_galerkin_field_noops_below_tolerance():
    mesh = HPMesh.uniform(0.0, 2.0, cells=2, degree=2)
    field = GalerkinField.project(mesh, lambda x: 1.0 + 0.0 * x)

    adapted = adapt_galerkin_field(field, tolerance=0.9)

    assert not adapted.changed
    assert adapted.field.mesh.dofs == field.mesh.dofs
