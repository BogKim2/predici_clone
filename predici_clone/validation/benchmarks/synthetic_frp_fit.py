from __future__ import annotations

from predici_clone.api import IntegrationControl, OutputConfig, Project, Recipe
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.generic_outputs import compute_generic_outputs
from predici_clone.postprocess.parameter_estimation import FittingProblem, OutputTarget, ParameterSpec, fit_generic_parameters, global_search_generic_parameters


def synthetic_parameter_recovery() -> dict[str, float]:
    true_project = Project(
        recipe=Recipe(integration=IntegrationControl(t_final=0.8, output_points=5)),
        outputs=OutputConfig(enabled_generic_outputs=("mass",)),
        generic_parameters={"GP_kp": 0.16},
    )
    target = compute_generic_outputs(SimulationEngine(true_project).run(), true_project.outputs)["mass"]
    base = Project(
        recipe=true_project.recipe,
        outputs=true_project.outputs,
        generic_parameters={"GP_kp": 0.05},
    )
    problem = FittingProblem(
        project=base,
        parameters=(ParameterSpec("GP_kp", 0.05, 0.01, 0.5),),
        targets=(OutputTarget("mass", target, 10.0),),
    )
    local = fit_generic_parameters(problem)
    global_result = global_search_generic_parameters(problem, method="dual_annealing", maxiter=8, seed=3)
    return {
        "target": float(target),
        "local_kp": local.parameters["GP_kp"],
        "global_kp": global_result.parameters["GP_kp"],
        "local_residual": local.residual_norm,
        "global_residual": global_result.residual_norm,
    }
