import numpy as np

from predici_clone.kinetics import RateLaw, ReactionKind, ReactionStep
from predici_clone.kinetics.rate_terms import (
    assemble_reaction_network_rhs,
    chain_transfer,
    scission,
    termination_combination,
)


def test_termination_combination_creates_longer_chains():
    y = np.zeros(8)
    y[2] = 1.0
    dy = termination_combination(y, rate=0.2)

    assert dy[2] < 0.0
    assert dy[4] > 0.0


def test_chain_transfer_moves_mass_to_target_length():
    y = np.zeros(5)
    y[3] = 2.0
    dy = chain_transfer(y, rate=0.5, target_length=0)

    assert dy[3] < 0.0
    assert dy[0] > 0.0
    np.testing.assert_allclose(np.sum(dy), 0.0)


def test_scission_splits_long_chains():
    y = np.zeros(8)
    y[1] = 2.0
    y[6] = 1.0
    dy = scission(y, rate=0.3)

    assert dy[1] == 0.0
    assert dy[6] < 0.0
    assert dy[3] > 0.0
    assert np.sum(dy) > 0.0


def test_reaction_network_rhs_uses_step_parameters():
    y = np.zeros(8)
    y[2] = 1.0
    steps = (
        ReactionStep(
            name="combination",
            kind=ReactionKind.TERMINATION_COMBINATION,
            reactants=("R", "R"),
            products=("P",),
            rate_law=RateLaw("GP_kt", ("GP_kt",)),
        ),
        ReactionStep(
            name="transfer",
            kind=ReactionKind.CHAIN_TRANSFER_TO_MONOMER,
            reactants=("R", "M"),
            products=("P0",),
            rate_law=RateLaw("GP_ctr", ("GP_ctr",)),
        ),
    )
    dy = assemble_reaction_network_rhs(y, steps, {"GP_kt": 0.2, "GP_ctr": 0.1})

    assert dy[0] > 0.0
    assert dy[4] > 0.0
