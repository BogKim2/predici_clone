from __future__ import annotations

from dataclasses import dataclass

import pandas as pd
import numpy as np

from predici_clone.api.project_schema import Project
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.generic_outputs import compute_generic_outputs
from predici_clone.postprocess.parameter_estimation import _with_generic_parameters


@dataclass(frozen=True)
class SensitivityParameter:
    name: str
    mean: float
    std: float


def sigma_point_sensitivity(project: Project, parameters: tuple[SensitivityParameter, ...]) -> pd.DataFrame:
    rows = []

    def run_case(label: str, values: dict[str, float]) -> None:
        case_project = _with_generic_parameters(project, values)
        result = SimulationEngine(case_project).run()
        outputs = compute_generic_outputs(result, case_project.outputs)
        row = {"case": label, **values, **outputs}
        rows.append(row)

    base_values = {param.name: param.mean for param in parameters}
    run_case("base", base_values)
    for param in parameters:
        high = dict(base_values)
        high[param.name] = param.mean + param.std
        run_case(f"{param.name}+", high)
        low = dict(base_values)
        low[param.name] = param.mean - param.std
        run_case(f"{param.name}-", low)
    return pd.DataFrame(rows)


def sensitivity_summary(frame: pd.DataFrame, output: str) -> pd.DataFrame:
    base = float(frame.loc[frame["case"] == "base", output].iloc[0])
    rows = []
    for _, row in frame.iterrows():
        if row["case"] == "base":
            continue
        rows.append({"case": row["case"], "output": output, "delta": float(row[output]) - base})
    return pd.DataFrame(rows)


def monte_carlo_sensitivity(
    project: Project,
    parameters: tuple[SensitivityParameter, ...],
    *,
    samples: int = 32,
    seed: int = 1,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []
    for index in range(samples):
        values = {
            param.name: float(rng.normal(param.mean, param.std))
            for param in parameters
        }
        case_project = _with_generic_parameters(project, values)
        result = SimulationEngine(case_project).run()
        outputs = compute_generic_outputs(result, case_project.outputs)
        rows.append({"case": f"mc_{index + 1}", **values, **outputs})
    return pd.DataFrame(rows)


def grid_sensitivity(
    project: Project,
    parameters: tuple[SensitivityParameter, ...],
    *,
    levels: int = 3,
) -> pd.DataFrame:
    if not 1 <= len(parameters) <= 3:
        raise ValueError("grid_sensitivity supports one to three parameters")
    if levels < 2:
        raise ValueError("levels must be at least 2")

    grids = [
        np.linspace(param.mean - param.std, param.mean + param.std, int(levels))
        for param in parameters
    ]
    rows = []
    for index, values_tuple in enumerate(np.array(np.meshgrid(*grids, indexing="ij")).T.reshape(-1, len(parameters))):
        values = {
            param.name: float(value)
            for param, value in zip(parameters, values_tuple)
        }
        case_project = _with_generic_parameters(project, values)
        result = SimulationEngine(case_project).run()
        outputs = compute_generic_outputs(result, case_project.outputs)
        rows.append({"case": f"grid_{index + 1}", **values, **outputs})
    return pd.DataFrame(rows)
