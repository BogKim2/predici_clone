from predici_clone.api import Project
from predici_clone.engine import SimulationEngine
from predici_clone.kinetics.reaction import ReactionKind
from predici_clone.kinetics.reaction_builder import (
    build_general_kinetic_step,
    build_polymer_reaction_step,
    filter_reaction_patterns,
)


def test_reaction_pattern_filter_finds_polymer_and_kinetic_templates():
    polymer_names = [pattern.name for pattern in filter_reaction_patterns("termination", category="polymer")]
    kinetic_names = [pattern.name for pattern in filter_reaction_patterns("mass-action")]

    assert "TerminationCombination" in polymer_names
    assert "GeneralKinetic" in kinetic_names


def test_build_polymer_reaction_step_declares_species_and_parameter():
    project = build_polymer_reaction_step(
        Project(),
        pattern_name="Propagation",
        reactants=("R", "M"),
        products=("R",),
        parameter="GP_kp",
        site="bulk",
    )

    assert project.reaction_steps[0].kind == ReactionKind.PROPAGATION
    assert project.reaction_steps[0].site == "bulk"
    assert project.generic_parameters["GP_kp"] == 0.0
    assert [item["name"] for item in project.substances] == ["R", "M"]


def test_build_general_kinetic_step_runs_with_independent_reaction_order():
    project = build_general_kinetic_step(
        Project(general_initial_conditions={"A": 1.0, "B": 0.0}),
        name="A_to_B",
        reactants=(("A", 1.0, 2.0),),
        products=(("B", 1.0),),
        forward_parameter="k1",
        backward_parameter="0",
    )
    project = Project.from_dict(project.to_dict())
    project.generic_parameters["k1"] = 0.4

    result = SimulationEngine(project).run()

    assert project.general_kinetic_steps[0].reactants[0].order == 2.0
    assert result.metadata["backend"] == "general_kinetics"
    assert result.metadata["final_concentrations"]["B"] > 0.0
