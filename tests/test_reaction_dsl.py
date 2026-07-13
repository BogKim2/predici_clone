import pytest
import numpy as np

from predici_clone.kinetics import RateLaw, ReactionKind, ReactionStep, StepTemplate
from predici_clone.kinetics.rate_terms import assemble_reaction_network_rhs, branching, polymer_partition


def test_step_template_requires_generic_parameter_bindings():
    template = StepTemplate(
        name="propagation",
        kind=ReactionKind.PROPAGATION,
        rate_expression="GP_kp * M * R",
        generic_parameters=("GP_kp",),
    )

    step = template.instantiate(
        site="site_a",
        reactants=("R", "M"),
        products=("R",),
        bindings={"GP_kp": 0.1},
        reactor_scope="reactor_1",
    )

    assert step.name == "propagation:site_a"
    assert step.rate_law.parameters == ("GP_kp",)
    assert step.reactor_scope == "reactor_1"

    with pytest.raises(ValueError):
        template.instantiate(site="site_b", reactants=("R",), products=("R",), bindings={})


def test_branching_operator_moves_material_to_longer_effective_lengths():
    distribution = np.zeros(8)
    distribution[2] = 1.0

    rhs = branching(distribution, rate=0.5)

    assert rhs[2] < 0.0
    assert rhs[4] > 0.0
    np.testing.assert_allclose(np.sum(rhs), 0.0)


def test_polymer_partition_operator_conserves_total_distribution():
    distribution = np.zeros(9)
    distribution[2] = 1.0
    distribution[7] = 0.5

    rhs = polymer_partition(distribution, rate=0.3, cutoff=4)

    assert np.linalg.norm(rhs) > 0.0
    np.testing.assert_allclose(np.sum(rhs), 0.0)


def test_reaction_network_dispatches_branching_and_polymer_partition_steps():
    distribution = np.zeros(9)
    distribution[2] = 1.0
    steps = (
        ReactionStep("branch", ReactionKind.BRANCHING, ("P",), ("P_branch",), RateLaw("GP_branch", ("GP_branch",))),
        ReactionStep("partition", ReactionKind.POLYMER_PARTITION, ("P",), ("P_phase",), RateLaw("GP_part", ("GP_part",))),
    )

    rhs = assemble_reaction_network_rhs(distribution, steps, {"GP_branch": 0.2, "GP_part": 0.1})

    assert np.linalg.norm(rhs) > 0.0
    np.testing.assert_allclose(np.sum(rhs), 0.0)
