import numpy as np

from predici_clone.core.basis_2d import TensorDistribution2D, flory_chain_distribution
from predici_clone.kinetics.copolymer_terms import TerminalModel, mayo_lewis_instantaneous_fraction, terminal_model_distribution


def test_tensor_distribution_single_composition_matches_chain_distribution():
    chain = flory_chain_distribution(0.6, 8)
    distribution = TensorDistribution2D.from_outer(chain, np.asarray([1.0]))

    np.testing.assert_allclose(distribution.chain_marginal(), chain)
    assert distribution.mean_composition() == 0.0


def test_terminal_model_distribution_matches_mayo_lewis_mean_composition():
    model = TerminalModel(r1=0.5, r2=2.0)
    expected = mayo_lewis_instantaneous_fraction(0.4, model)

    distribution = terminal_model_distribution(
        feed_fraction_1=0.4,
        r1=model.r1,
        r2=model.r2,
        propagation_probability=0.5,
        nmax=12,
        composition_bins=9,
    )

    assert distribution.density.shape == (12, 9)
    assert abs(distribution.mean_composition() - expected) < 1e-12
    np.testing.assert_allclose(np.sum(distribution.density), 1.0)
