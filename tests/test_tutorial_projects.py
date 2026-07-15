import numpy as np

from predici_clone.api import load_project, save_project
from predici_clone.engine import SimulationCallbacks, SimulationEngine
from predici_clone.validation.tutorial_projects import (
    oregonator_kinetics_project,
    polyethylene_basic_project,
)


def test_polyethylene_tutorial_project_roundtrips_and_runs(tmp_path):
    project = polyethylene_basic_project()
    path = tmp_path / "polyethylene.predici.json"
    save_project(project, path)
    loaded = load_project(path)

    assert loaded.name == "Tutorial: Polyethylene Basic Model"
    assert loaded.substances[1]["name"] == "E"
    assert loaded.polymers[0]["name"] == "R"
    assert {step.name for step in loaded.reaction_steps} >= {
        "initiator_decay",
        "propagation",
        "termination_combination",
        "termination_disproportionation",
    }

    result = SimulationEngine(loaded).run()

    assert result.success
    assert result.metadata["backend"] == "discrete"
    assert result.final_distribution.size == loaded.reactor.nmax + 1
    assert result.final_moments.mass >= 0.0
    assert result.time[-1] == loaded.recipe.integration.t_final


def test_oregonator_tutorial_project_roundtrips_and_runs_general_kinetics(tmp_path):
    project = oregonator_kinetics_project(corrected_order=True)
    path = tmp_path / "oregonator.predici.json"
    save_project(project, path)
    loaded = load_project(path)

    assert loaded.general_kinetic_steps[3].reactants[0].order == 2.0
    assert loaded.general_initial_conditions["B"] == 0.1

    progress = []
    steps = []
    result = SimulationEngine(loaded).run(
        callbacks=SimulationCallbacks(
            on_progress=progress.append,
            on_step=steps.append,
        )
    )

    assert result.success
    assert result.metadata["backend"] == "general_kinetics"
    assert result.metadata["species_names"] == ["A", "B", "C", "D", "E"]
    assert set(result.metadata["final_concentrations"]) == {"A", "B", "C", "D", "E"}
    assert result.state_history.shape == (5, loaded.recipe.integration.output_points)
    assert np.all(result.state_history >= 0.0)
    assert steps and "conc:A" in steps[-1]
    assert progress[-1] == 1.0


def test_oregonator_corrected_order_changes_concentration_trajectory():
    uncorrected = SimulationEngine(oregonator_kinetics_project(corrected_order=False)).run()
    corrected = SimulationEngine(oregonator_kinetics_project(corrected_order=True)).run()
    c_index = corrected.metadata["species_names"].index("C")
    d_index = corrected.metadata["species_names"].index("D")

    assert corrected.success
    assert uncorrected.success
    assert not np.allclose(corrected.state_history[c_index], uncorrected.state_history[c_index])
    assert abs(float(corrected.state_history[d_index, -1] - uncorrected.state_history[d_index, -1])) > 1e-4
    assert float(corrected.state_history[c_index, -1]) >= 0.0
