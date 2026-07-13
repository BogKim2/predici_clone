from predici_clone.api import IntegrationControl, OutputConfig, Project, ReactorConfig, Recipe, activate_detailed_iteration
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.generic_outputs import compute_generic_outputs


def test_activate_detailed_iteration_tunes_generic_parameter_to_target():
    base = Project(
        reactor=ReactorConfig(kind="Batch", nmax=30),
        recipe=Recipe(integration=IntegrationControl(t_final=2.0, output_points=8)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
    )
    target_project = Project(
        reactor=base.reactor,
        kinetics=base.kinetics,
        recipe=base.recipe,
        outputs=base.outputs,
        generic_parameters={"GP_kp": base.kinetics.kp * 1.5},
    )
    target = compute_generic_outputs(SimulationEngine(target_project).run(), target_project.outputs)["mass"]

    result = activate_detailed_iteration(
        base,
        target_output="mass",
        target_value=target,
        tune_parameter="GP_kp",
        initial=base.kinetics.kp,
        lower=0.001,
        upper=1.0,
        weight=100000.0,
    )

    assert result.success
    assert result.residual_norm < 1e-5
