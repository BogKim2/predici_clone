import numpy as np

from predici_clone.core.error_estimator import mark_largest, modal_tail_indicator
from predici_clone.core.galerkin import GalerkinField
from predici_clone.core.grid import HPMesh
from predici_clone.core.moments import from_galerkin


def test_polynomial_projection_and_moments_are_accurate():
    mesh = HPMesh.uniform(0.0, 2.0, cells=2, degree=2)
    field = GalerkinField.project(mesh, lambda x: 1.0 + 2.0 * x + x * x)

    x = np.linspace(0.0, 2.0, 17)
    np.testing.assert_allclose(field.evaluate(x), 1.0 + 2.0 * x + x * x, atol=1e-12)

    report = from_galerkin(field)
    np.testing.assert_allclose(report.m0, 26.0 / 3.0, atol=1e-12)
    np.testing.assert_allclose(report.m1, 34.0 / 3.0, atol=1e-12)
    np.testing.assert_allclose(report.m2, 256.0 / 15.0, atol=1e-12)


def test_h_and_p_refinement_preserve_integral():
    mesh = HPMesh.uniform(0.0, 4.0, cells=2, degree=1)
    field = GalerkinField.project(mesh, lambda x: np.exp(-x))
    original_m0 = field.moment(0)

    h_refined = field.h_refined({0})
    p_refined = h_refined.p_refined({1}, amount=2)

    np.testing.assert_allclose(h_refined.moment(0), original_m0, rtol=2e-4)
    np.testing.assert_allclose(p_refined.moment(0), h_refined.moment(0), rtol=2e-4)


def test_modal_tail_marks_non_smooth_cell():
    mesh = HPMesh.uniform(0.0, 2.0, cells=2, degree=3)
    field = GalerkinField.project(mesh, lambda x: np.where(x < 1.0, x, 5.0 - x))

    indicators = modal_tail_indicator(field)
    marked = mark_largest(indicators, fraction=0.5)

    assert len(marked) == 1
    assert max(indicators) > 0.0
