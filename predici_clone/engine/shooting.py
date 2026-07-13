from __future__ import annotations

from dataclasses import dataclass

from predici_clone.api.project_schema import Project
from predici_clone.postprocess.parameter_estimation import FittingProblem, OutputTarget, ParameterSpec, fit_generic_parameters


@dataclass(frozen=True)
class ShootingControl:
    target_output: str
    target_value: float
    tune_parameter: str
    initial: float
    lower: float
    upper: float
    weight: float = 1.0


def activate_detailed_iteration(project: Project, control: ShootingControl):
    problem = FittingProblem(
        project=project,
        parameters=(
            ParameterSpec(
                name=control.tune_parameter,
                initial=control.initial,
                lower=control.lower,
                upper=control.upper,
            ),
        ),
        targets=(OutputTarget(control.target_output, control.target_value, control.weight),),
    )
    return fit_generic_parameters(problem)
