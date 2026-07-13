import numpy as np

from predici_clone.api import FeedStream, InitialConditions, IntegrationControl, Project, ReactorConfig, Recipe, append_pre_schedule_step
from predici_clone.engine import SimulationEngine
from predici_clone.engine.galerkin_backend import project_distribution_history


def test_project_distribution_history_reconstructs_shape_and_moments():
    history = np.zeros((21, 4))
    history[2:8, :] = np.linspace(1.0, 2.0, 4)
    projected = project_distribution_history(history, first_length=0, cells=4, degree=2)

    assert projected.reconstructed_history.shape == history.shape
    assert projected.coefficients.shape[1] == history.shape[1]
    assert projected.final_error_indicators.size == projected.mesh.cells
    np.testing.assert_allclose(projected.reconstructed_history.sum(axis=0), history.sum(axis=0), rtol=0.25)


def test_engine_galerkin_backend_returns_reconstructed_distribution():
    common = dict(reactor=ReactorConfig(kind="Batch", nmax=60))
    discrete = Project(
        **common,
        recipe=Recipe(integration=IntegrationControl(t_final=2.0, output_points=8, backend="discrete")),
    )
    galerkin = Project(
        **common,
        recipe=Recipe(integration=IntegrationControl(t_final=2.0, output_points=8, backend="galerkin", galerkin_cells=8, galerkin_degree=2)),
    )

    discrete_result = SimulationEngine(discrete).run()
    galerkin_result = SimulationEngine(galerkin).run()

    assert galerkin_result.metadata["backend"] == "galerkin"
    assert "galerkin_error_max" in galerkin_result.metadata
    assert galerkin_result.final_distribution.shape == discrete_result.final_distribution.shape
    np.testing.assert_allclose(galerkin_result.final_moments.mass, discrete_result.final_moments.mass, rtol=0.35)


def test_engine_galerkin_direct_backend_runs_batch_coefficients():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=40),
        recipe=Recipe(
            initial=InitialConditions(monomer=2.0, initiator=0.1, radicals=0.01),
            integration=IntegrationControl(t_final=2.0, output_points=8, backend="galerkin_direct", galerkin_cells=6, galerkin_degree=2),
        ),
    )

    result = SimulationEngine(project).run()

    assert result.success
    assert result.metadata["backend"] == "galerkin_direct"
    assert result.metadata["species_coupled"]
    assert result.final_distribution.size == 41
    assert result.final_moments.m0 > 0.0
    assert result.state_history[0, -1] < result.state_history[0, 0]
    assert result.state_history[1, -1] < result.state_history[1, 0]


def test_engine_galerkin_direct_adaptive_loop_records_mesh_events():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=40),
        recipe=Recipe(
            initial=InitialConditions(monomer=2.0, initiator=0.1, radicals=0.02),
            integration=IntegrationControl(t_final=3.0, output_points=6, backend="galerkin_direct", galerkin_cells=3, galerkin_degree=1),
        ),
        generic_parameters={
            "adaptive_galerkin": 1.0,
            "adaptive_tolerance": 0.0,
            "adaptive_max_degree": 3.0,
            "adaptive_max_cells": 12.0,
        },
    )

    result = SimulationEngine(project).run()

    assert result.success
    assert result.metadata["adaptive_galerkin"]
    assert result.metadata["adaptive_event_count"] >= 1
    assert result.metadata["galerkin_dofs"] > project.recipe.integration.galerkin_cells * (project.recipe.integration.galerkin_degree + 1)
    assert len(result.metadata["galerkin_dof_history"]) == result.time.size
    assert result.final_distribution.size == 41


def test_engine_galerkin_direct_backend_runs_semibatch_coefficients_and_volume():
    project = Project(
        reactor=ReactorConfig(kind="Semi-batch", nmax=30, volume=1.0),
        recipe=Recipe(
            initial=InitialConditions(monomer=0.4, initiator=0.05, radicals=0.01),
            feed=FeedStream(monomer=2.0, initiator=0.1, rate=0.08),
            integration=IntegrationControl(t_final=2.0, output_points=6, backend="galerkin_direct", galerkin_cells=5, galerkin_degree=2),
        ),
    )
    project = append_pre_schedule_step(project, 1.0, "set_feed_rate", rate=0.2)

    result = SimulationEngine(project).run()

    assert result.success
    assert result.metadata["backend"] == "galerkin_direct"
    assert result.metadata["volume_coupled"]
    assert result.final_distribution.size == 31
    assert result.state_history[-1, -1] > result.state_history[-1, 0]
    assert result.metadata["scheduled_final_feed_rate"] == 0.2


def test_engine_galerkin_direct_backend_runs_cstr_with_scheduled_residence_time():
    project = Project(
        reactor=ReactorConfig(kind="CSTR", nmax=30, residence_time=4.0),
        recipe=Recipe(
            initial=InitialConditions(monomer=0.5, initiator=0.04, radicals=0.01),
            feed=FeedStream(monomer=2.0, initiator=0.1, rate=0.0),
            integration=IntegrationControl(t_final=2.0, output_points=6, backend="galerkin_direct", galerkin_cells=5, galerkin_degree=2),
        ),
    )
    project = append_pre_schedule_step(project, 1.0, "set_residence_time", value=1.5)

    result = SimulationEngine(project).run()

    assert result.success
    assert result.metadata["backend"] == "galerkin_direct"
    assert result.metadata["residence_time_coupled"]
    assert result.metadata["scheduled_final_residence_time"] == 1.5
    assert result.final_distribution.size == 31
    assert result.state_history[0, -1] != result.state_history[0, 0]


def test_engine_galerkin_direct_backend_runs_cascade_and_pfr_stages():
    base_recipe = Recipe(
        initial=InitialConditions(monomer=0.5, initiator=0.04, radicals=0.01),
        integration=IntegrationControl(t_final=1.5, output_points=5, backend="galerkin_direct", galerkin_cells=4, galerkin_degree=2),
    )
    cascade = Project(reactor=ReactorConfig(kind="Cascade", nmax=24, residence_time=5.0, stages=3), recipe=base_recipe)
    pfr = Project(reactor=ReactorConfig(kind="PFR", nmax=24, residence_time=5.0, axial_cells=4), recipe=base_recipe)

    cascade_result = SimulationEngine(cascade).run()
    pfr_result = SimulationEngine(pfr).run()

    assert cascade_result.success
    assert pfr_result.success
    assert cascade_result.metadata["galerkin_direct_stages"] == 3
    assert pfr_result.metadata["galerkin_direct_stages"] == 4
    assert cascade_result.final_distribution.size == 25
    assert pfr_result.final_distribution.size == 25
