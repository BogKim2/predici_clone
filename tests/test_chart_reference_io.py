import numpy as np

from predici_clone.postprocess.charting import (
    ChartConfig,
    ReferenceCurve,
    distribution_chart_profile,
    gpc_tail_weights,
    import_gpc_data,
    load_reference_curve,
    load_structured_dump,
    save_reference_curve,
    save_structured_dump,
    weighted_curve_residual,
)


def test_chart_config_gpc_mode_uses_log_weight_definition():
    distribution = np.asarray([0.0, 2.0, 1.0])
    profile = distribution_chart_profile(
        distribution,
        ChartConfig(distribution_y_axis="gpc", x_axis_scale="logarithmic"),
        monomer_mw=50.0,
    )

    assert profile.x_label == "log10 molecular weight"
    assert profile.y_label == "W(log M)"
    np.testing.assert_allclose(np.sum(profile.y), 1.0)
    assert profile.y[-1] > profile.y[1]


def test_reference_curve_dat_roundtrip(tmp_path):
    path = tmp_path / "reference.dat"
    curve = ReferenceCurve(np.asarray([1.0, 2.0]), np.asarray([0.2, 0.8]), label="run")

    save_reference_curve(curve, path)
    loaded = load_reference_curve(path, label="run")

    np.testing.assert_allclose(loaded.x, curve.x)
    np.testing.assert_allclose(loaded.y, curve.y)
    assert loaded.label == "run"


def test_structured_dump_roundtrip(tmp_path):
    path = tmp_path / "chart_dump.npz"

    save_structured_dump(path, time=np.asarray([0.0, 1.0]), value=np.asarray([2.0, 3.0]))
    loaded = load_structured_dump(path)

    np.testing.assert_allclose(loaded["time"], [0.0, 1.0])
    np.testing.assert_allclose(loaded["value"], [2.0, 3.0])


def test_import_gpc_data_reads_two_column_csv(tmp_path):
    path = tmp_path / "gpc.csv"
    path.write_text("logM,W\n2.0,0.1\n3.0,0.9\n", encoding="utf-8")

    curve = import_gpc_data(path)

    np.testing.assert_allclose(curve.x, [2.0, 3.0])
    np.testing.assert_allclose(curve.y, [0.1, 0.9])


def test_gpc_tail_weighting_emphasizes_high_molecular_weight_tail():
    x = np.asarray([1.0, 2.0, 3.0])
    weights = gpc_tail_weights(x, strength=2.0)
    residual = weighted_curve_residual([0.0, 0.0, 0.0], [1.0, 1.0, 1.0], weighting="gpc_tail", x=x)

    assert weights[0] == 1.0
    assert weights[-1] == 3.0
    np.testing.assert_allclose(residual, -weights)
