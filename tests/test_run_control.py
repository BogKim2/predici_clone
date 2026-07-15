import numpy as np

from predici_clone.api import IntegrationControl, Project, ReactorConfig, Recipe
from predici_clone.engine import SimulationEngine, SimulationRequest


def _project() -> Project:
    return Project(
        reactor=ReactorConfig(kind="Batch", nmax=20),
        recipe=Recipe(integration=IntegrationControl(t_final=2.0, output_points=9)),
    )


def test_run_to_time_stops_at_requested_time_and_exposes_actual_values():
    result = SimulationEngine(_project()).run_to_time(0.5)

    assert result.success
    assert result.time[-1] == 0.5
    assert result.metadata["run_control"]["target_time"] == 0.5
    assert result.metadata["actual_values"][-1]["time"] == 0.5
    assert result.metadata["n_variables"] == result.state_history.shape[0]


def test_single_step_advances_by_default_output_interval():
    engine = SimulationEngine(_project())

    first = engine.single_step()
    second = engine.single_step()

    assert first.metadata["run_control"]["requested_step"] is True
    assert first.time[-1] == 0.25
    assert second.time[-1] == 0.5


def test_run_to_time_final_matches_full_run():
    project = _project()
    engine = SimulationEngine(project)

    engine.run_to_time(0.5)
    resumed = engine.run_to_time(project.recipe.integration.t_final)
    full = SimulationEngine(project).run()

    assert np.allclose(resumed.state_history[:, -1], full.state_history[:, -1])
    assert np.allclose(resumed.final_distribution, full.final_distribution)


def test_simulation_mode_flags_are_recorded_in_result_metadata():
    project = Project(
        recipe=Recipe(
            integration=IntegrationControl(
                t_final=1.0,
                output_points=5,
                simulation_mode="moments",
                include_monte_carlo=True,
                use_tau_leaping=True,
            )
        )
    )

    result = SimulationEngine(project).run(SimulationRequest(mode="moments"))

    assert result.metadata["simulation_mode"] == "moments"
    assert result.metadata["include_monte_carlo"] is True
    assert result.metadata["use_tau_leaping"] is True


def test_moments_mode_returns_reduced_moment_state_close_to_distribution_run():
    moments_project = Project(
        recipe=Recipe(integration=IntegrationControl(t_final=1.0, output_points=5, simulation_mode="moments"))
    )
    distribution_project = Project(
        recipe=Recipe(integration=IntegrationControl(t_final=1.0, output_points=5, simulation_mode="distributions"))
    )

    moments = SimulationEngine(moments_project).run()
    distributions = SimulationEngine(distribution_project).run()

    assert moments.metadata["moments_backend"] == "projected_distribution_moments"
    assert tuple(moments.metadata["moment_state_names"]) == ("M0", "M1", "M2", "Mn", "Mw", "PDI")
    assert moments.state_history.shape[0] == 6
    assert moments.metadata["actual_values"][-1]["n_variables"] == 6
    np.testing.assert_allclose(moments.final_moments.mn, distributions.final_moments.mn)
    np.testing.assert_allclose(moments.final_moments.mw, distributions.final_moments.mw)


def test_monte_carlo_and_tau_leaping_modes_record_numerical_summaries():
    project = Project(
        recipe=Recipe(
            integration=IntegrationControl(
                t_final=1.0,
                output_points=5,
                include_monte_carlo=True,
                use_tau_leaping=True,
            )
        ),
        generic_parameters={"monte_carlo_ensemble_size": 4.0, "monte_carlo_seed": 7.0},
    )

    first = SimulationEngine(project).run()
    second = SimulationEngine(project).run()

    assert first.metadata["monte_carlo_backend"] == "poisson_ensemble_projection"
    assert first.metadata["monte_carlo_ensemble_size"] == 4
    assert len(first.metadata["monte_carlo_final_mean"]) == first.final_distribution.size
    assert first.metadata["monte_carlo_final_mean"] == second.metadata["monte_carlo_final_mean"]
    assert first.metadata["tau_leaping_backend"] == "rounded_distribution_projection"
    assert first.metadata["tau_leaping_tau"] > 0.0
    assert len(first.metadata["tau_leaping_final_distribution"]) == first.final_distribution.size
