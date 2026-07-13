import numpy as np

from predici_clone.api import (
    FeedProfile,
    FlowDist,
    Project,
    ReactorConfig,
    Recipe,
    IntegrationControl,
    OutputConfig,
    execute_public_command,
    export_c_moment_equations,
    export_matlab_moment_equations,
    flow_solve,
    fluid_balance,
)
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.generic_outputs import compute_generic_outputs


def test_matlab_and_c_moment_equation_exports_are_writable(tmp_path):
    project = Project(generic_parameters={"GP_kp": 0.12})
    matlab_path = tmp_path / "moments.m"
    c_path = tmp_path / "moments.c"

    matlab = export_matlab_moment_equations(project, matlab_path)
    c_code = export_c_moment_equations(project, c_path)

    assert "function dydt = predici_moments" in matlab
    assert "kp = 0.12" in matlab
    assert "void predici_moments" in c_code
    assert "dydt[6]" in c_code
    assert matlab_path.read_text(encoding="utf-8") == matlab
    assert c_path.read_text(encoding="utf-8") == c_code


def test_public_command_dispatcher_covers_ole_style_project_and_result_commands():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=10),
        recipe=Recipe(integration=IntegrationControl(t_final=0.5, output_points=4)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
    )
    result = SimulationEngine(project).run()

    created = execute_public_command("CreateRecipe", project=project, recipe_name="recipe_copy")
    points = execute_public_command("GetDistPoints", result=result, log_axis=True)
    moments = execute_public_command("GetDistMoments", result=result)
    pressure = execute_public_command("GetReactorPressure", result=result)
    changed = execute_public_command("SetFeedRate", project=project, rate=0.33)
    lumped = execute_public_command("SetDistLumping", project=project, on_off=True)
    enthalpy_project = execute_public_command("SetEnthalpy", project=project, value=-12.0)
    heat_project = execute_public_command(
        "SetHeatExchanger",
        project=project,
        use_heat_exchanger=True,
        heat_transfer=1.0,
        area=1.0,
        heat_capacity=4.0,
        mass_flow=1.0,
        mass_holdup=1.0,
        initial_feed_temp=300.0,
    )
    shooting = execute_public_command(
        "ActivateDetailedIteration",
        project=project,
        target_output="mass",
        target_value=compute_generic_outputs(result, project.outputs)["mass"],
        tune_parameter="GP_kp",
        initial=project.kinetics.kp,
        lower=0.001,
        upper=1.0,
        weight=100000.0,
    )

    assert created.recipe.name == "recipe_copy"
    assert points.shape == (11, 2)
    assert "Mw" in moments
    assert pressure == 1.0
    assert changed.recipe.feed.rate == 0.33
    assert lumped.generic_parameters["dist_lumping"] == 1.0
    assert enthalpy_project.heat_balance.enabled
    assert execute_public_command("CheckEnthalpy", project=heat_project)
    assert shooting.success


def test_feed_profile_flow_dist_and_fluid_balance_helpers():
    profile = FeedProfile(((0.0, 1.0), (1.0, 3.0), (2.0, 5.0)))
    dist = FlowDist.from_samples([0.0, 1.0, 2.0], [1.0, 2.0, 1.0])
    balance = fluid_balance(inventory=10.0, inflow=2.5, outflow=1.0)

    assert profile.value_at(0.5) == 2.0
    np.testing.assert_allclose(np.sum(dist.weights), 1.0)
    assert flow_solve(profile, dist) == 3.0
    assert balance.accumulation == 1.5


def test_generic_outputs_include_mfi_scalar():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=12),
        recipe=Recipe(integration=IntegrationControl(t_final=0.6, output_points=4)),
        outputs=OutputConfig(enabled_generic_outputs=("MFI", "Mw")),
    )
    result = SimulationEngine(project).run()
    outputs = compute_generic_outputs(result, project.outputs)

    assert outputs["MFI"] == 1.0 / max(outputs["Mw"], 1e-12)
