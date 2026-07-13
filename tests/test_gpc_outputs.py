import numpy as np

from predici_clone.postprocess.gpc import distribution_to_gpc_profile, gaussian_convolution


def test_distribution_to_gpc_profile_supports_weight_and_log_axis():
    distribution = np.asarray([0.0, 2.0, 1.0, 0.5])

    profile = distribution_to_gpc_profile(
        distribution,
        first_length=0,
        monomer_mw=50.0,
        mode="weight",
        log_axis=True,
    )

    assert profile.x_label == "log10 molecular weight"
    assert profile.y_label == "weight fraction"
    np.testing.assert_allclose(np.sum(profile.y), 1.0)
    assert np.all(np.diff(profile.x) > 0)


def test_gpc_gaussian_convolution_preserves_total_signal():
    impulse = np.zeros(21)
    impulse[10] = 1.0

    broadened = gaussian_convolution(impulse, sigma=1.2)

    np.testing.assert_allclose(np.sum(broadened), 1.0)
    assert broadened[10] < 1.0
    assert broadened[9] > 0.0
