import numpy as np

from predici_clone.postprocess.fitting import fit_flory_probability
from predici_clone.validation.paper_benchmarks import moments_from_frame
from tests.paper_benchmarks import flory_step_growth_case, fogler_fractionation_case, multisite_schulz_flory_case


def test_fogler_fractionation_case_matches_reported_moments():
    case = fogler_fractionation_case()
    report = moments_from_frame(case.frame)

    np.testing.assert_allclose(report.mn, case.expected["Mn"])
    np.testing.assert_allclose(report.mw, case.expected["Mw"])
    np.testing.assert_allclose(report.pdi, case.expected["PDI"])


def test_flory_case_can_recover_probability_from_weight_fraction():
    case = flory_step_growth_case(probability=0.97, max_length=2000)
    probability = fit_flory_probability(
        case.frame["chain_length"].to_numpy(),
        case.frame["weight_fraction"].to_numpy(),
    )

    np.testing.assert_allclose(probability, 0.97, atol=2e-4)


def test_multisite_case_is_broader_than_single_site_flory():
    case = multisite_schulz_flory_case(max_length=3000)
    assert case.expected["PDI"] > 2.0
