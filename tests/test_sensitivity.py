from predici_clone.api import IntegrationControl, OutputConfig, Project, ReactorConfig, Recipe
from predici_clone.postprocess.sensitivity import (
    SensitivityParameter,
    grid_sensitivity,
    monte_carlo_sensitivity,
    sensitivity_summary,
    sigma_point_sensitivity,
)


def test_sigma_point_sensitivity_runs_2p_plus_1_cases():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=20),
        recipe=Recipe(integration=IntegrationControl(t_final=1.5, output_points=6)),
        outputs=OutputConfig(enabled_generic_outputs=("mass", "Mn")),
    )

    frame = sigma_point_sensitivity(
        project,
        (
            SensitivityParameter("GP_kp", mean=0.08, std=0.01),
            SensitivityParameter("GP_kd", mean=0.02, std=0.005),
        ),
    )
    summary = sensitivity_summary(frame, "mass")

    assert len(frame) == 5
    assert {"case", "GP_kp", "GP_kd", "mass", "Mn"} <= set(frame.columns)
    assert len(summary) == 4


def test_monte_carlo_sensitivity_is_seed_reproducible():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=16),
        recipe=Recipe(integration=IntegrationControl(t_final=1.0, output_points=5)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
    )
    params = (SensitivityParameter("GP_kp", mean=0.08, std=0.01),)

    first = monte_carlo_sensitivity(project, params, samples=4, seed=42)
    second = monte_carlo_sensitivity(project, params, samples=4, seed=42)

    assert len(first) == 4
    assert {"case", "GP_kp", "mass"} <= set(first.columns)
    assert first["GP_kp"].tolist() == second["GP_kp"].tolist()


def test_grid_sensitivity_runs_cartesian_variation_for_up_to_three_parameters():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=12),
        recipe=Recipe(integration=IntegrationControl(t_final=0.8, output_points=4)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
    )
    frame = grid_sensitivity(
        project,
        (
            SensitivityParameter("GP_kp", mean=0.08, std=0.01),
            SensitivityParameter("GP_kd", mean=0.02, std=0.004),
            SensitivityParameter("GP_kt", mean=0.05, std=0.006),
        ),
        levels=2,
    )

    assert len(frame) == 8
    assert {"case", "GP_kp", "GP_kd", "GP_kt", "mass"} <= set(frame.columns)
