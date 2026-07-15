import numpy as np

from predici_clone.kinetics.copolymer_terms import PenultimateModel, penultimate_probabilities, terminal_transition_matrix
from predici_clone.kinetics.fgd import counter_subdistribution
from predici_clone.kinetics.mechanisms.atrp import ATRPParameters, atrp_batch_summary
from predici_clone.kinetics.mechanisms.crosslink import CrosslinkModel
from predici_clone.kinetics.mechanisms.polycondensation import carothers_moments, schulz_flory_distribution


def test_atrp_molar_mass_is_linear_and_distribution_stays_narrow():
    conversion = np.linspace(0.1, 0.9, 9)
    result = atrp_batch_summary(conversion, ATRPParameters(100, 100, deactivation_rate=200))

    assert np.allclose(np.diff(result.number_average_molar_mass), np.diff(result.number_average_molar_mass)[0])
    assert np.max(result.dispersity) < 1.11


def test_polycondensation_matches_carothers_and_normalizes_distribution():
    distribution = schulz_flory_distribution(0.95, 1000)
    number_average, weight_average, dispersity = carothers_moments(0.95)

    assert np.isclose(distribution.sum(), 1.0)
    assert np.isclose(number_average, 20.0)
    assert np.isclose(weight_average / number_average, dispersity)
    assert np.isclose(dispersity, 1.95)


def test_crosslink_gel_point_and_functional_group_distribution():
    model = CrosslinkModel(3, 3)

    assert model.gel_conversion == 0.5
    assert model.gel_fraction(0.49) == 0
    assert model.gel_fraction(0.8) > 0
    assert np.isclose(sum(counter_subdistribution(4, 0.3).values()), 1.0)


def test_penultimate_and_n_monomer_models_produce_probabilities():
    coefficients = np.ones((3, 3, 3))
    coefficients[0, 1] = [1, 2, 3]
    probabilities = penultimate_probabilities(0, 1, np.asarray([0.2, 0.3, 0.5]), PenultimateModel(coefficients))
    terminal = terminal_transition_matrix(np.asarray([0.2, 0.3, 0.5]), np.ones((3, 3)))

    assert np.isclose(probabilities.sum(), 1.0)
    assert np.allclose(terminal.sum(axis=1), 1.0)
