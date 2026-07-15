import numpy as np

from predici_clone.psd.kernels import constant_agglomeration_kernel, normalized_nucleus_shape
from predici_clone.psd.pbe import PopulationBalanceModel, msmpr_analytic_profile
from predici_clone.psd.profile import PSDProfile


def test_profile_moments_and_msmpr_mean_match_analytic_limit():
    edges = np.linspace(0, 20, 2001)
    profile = msmpr_analytic_profile(edges, growth_rate=2.0, residence_time=1.5, nucleation_rate=4.0)

    assert np.isclose(profile.mean_size, 3.0, rtol=0.015)
    assert profile.total_volume > 0


def test_nucleation_and_growth_preserve_total_solute_crystal_mass():
    profile = PSDProfile.linear(0.01, 2.01, 200)
    model = PopulationBalanceModel(profile, solute_concentration=10.0, crystal_density=2.0)
    shape = normalized_nucleus_shape(profile.edges, 0.05, 0.01)
    model.nucleation_step(10.0, shape, 0.01)
    initial_mass = model.solute_concentration + model.crystal_density * model.profile.total_volume
    model.growth_step(0.02, 0.01)
    final_mass = model.solute_concentration + model.crystal_density * model.profile.total_volume

    assert np.isclose(final_mass, initial_mass, rtol=1e-10)


def test_agglomeration_reduces_number_and_conserves_volume():
    profile = PSDProfile.linear(0.1, 5.1, 100, density=1.0)
    model = PopulationBalanceModel(profile)
    initial_number = profile.moment(0)
    initial_volume = profile.total_volume
    model.agglomeration_step(constant_agglomeration_kernel(1e-3), 0.1)

    assert model.profile.moment(0) < initial_number
    assert np.isclose(model.profile.total_volume, initial_volume, rtol=1e-12)


def test_growth_expands_grid_when_front_reaches_boundary():
    profile = PSDProfile.linear(0.1, 1.1, 10)
    density = np.zeros(10)
    density[-1] = 1.0
    model = PopulationBalanceModel(profile.with_density(density))

    model.growth_step(0.1, 0.1)

    assert model.profile.number_density.size > 10
