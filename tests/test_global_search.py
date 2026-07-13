from predici_clone.api import IntegrationControl, OutputConfig, Project, ReactorConfig, Recipe
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.generic_outputs import compute_generic_outputs
from predici_clone.postprocess.parameter_estimation import FittingProblem, OutputTarget, ParameterSpec, global_search_generic_parameters


def test_global_search_generic_parameters_reduces_objective():
    base = Project(
        reactor=ReactorConfig(kind="Batch", nmax=20),
        recipe=Recipe(integration=IntegrationControl(t_final=1.5, output_points=6)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
    )
    target_project = Project(
        reactor=base.reactor,
        kinetics=base.kinetics,
        recipe=base.recipe,
        outputs=base.outputs,
        generic_parameters={"GP_kp": base.kinetics.kp * 1.4},
    )
    target = compute_generic_outputs(SimulationEngine(target_project).run(), target_project.outputs)["mass"]
    problem = FittingProblem(
        project=base,
        parameters=(ParameterSpec("GP_kp", initial=0.02, lower=0.001, upper=0.5),),
        targets=(OutputTarget("mass", target, weight=100000.0),),
    )

    result = global_search_generic_parameters(problem, maxiter=4, seed=2)

    assert result.success
    assert result.residual_norm < 0.05
