import pytest

from predici_clone.api import IntegrationControl, OutputConfig, Project, ReactorConfig, Recipe
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.experiment_data import (
    DataMapping,
    load_experiment_csv,
    residual_frame,
    trim_experiment,
)
from predici_clone.postprocess.generic_outputs import compute_generic_outputs


def _project(t_final: float) -> Project:
    return Project(
        reactor=ReactorConfig(kind="Batch", nmax=24),
        recipe=Recipe(integration=IntegrationControl(t_final=t_final, output_points=6)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
    )


def test_load_trim_and_residual_frame_for_synthetic_csv(tmp_path):
    project = _project(2.0)
    rows = []
    for time in (0.5, 1.0, 1.5):
        case = _project(time)
        outputs = compute_generic_outputs(SimulationEngine(case).run(), case.outputs)
        rows.append(f"{time},{outputs['mass']}")
    csv_path = tmp_path / "experiment.csv"
    csv_path.write_text("time,mass_obs\n" + "\n".join(rows), encoding="utf-8")

    dataset = load_experiment_csv(csv_path, name="synthetic")
    trimmed = trim_experiment(dataset, start=0.75, end=1.25)
    residuals = residual_frame(project, trimmed, (DataMapping("mass", "mass_obs", weight=100.0),))

    assert trimmed.frame["time"].tolist() == [1.0]
    assert residuals["experiment"].tolist() == ["synthetic"]
    assert residuals["output"].tolist() == ["mass"]
    assert abs(float(residuals["residual"].iloc[0])) < 1e-8


def test_load_experiment_csv_requires_time_column(tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("t,mass_obs\n1.0,2.0\n", encoding="utf-8")

    with pytest.raises(ValueError, match="Missing time column"):
        load_experiment_csv(csv_path)
