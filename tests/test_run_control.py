import numpy as np

from predici_clone.api import IntegrationControl, Project, ReactorConfig, Recipe
from predici_clone.engine import SimulationEngine


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
