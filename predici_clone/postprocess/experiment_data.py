from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from predici_clone.api.project_schema import IntegrationControl, Project, Recipe
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.generic_outputs import compute_generic_outputs


@dataclass(frozen=True)
class DataMapping:
    output: str
    column: str
    weight: float = 1.0


@dataclass(frozen=True)
class ExperimentDataset:
    name: str
    frame: pd.DataFrame
    time_column: str = "time"


def load_experiment_csv(path: str | Path, *, name: str | None = None, time_column: str = "time") -> ExperimentDataset:
    frame = pd.read_csv(path)
    if time_column not in frame.columns:
        raise ValueError(f"Missing time column: {time_column}")
    return ExperimentDataset(name=name or Path(path).stem, frame=frame, time_column=time_column)


def trim_experiment(dataset: ExperimentDataset, *, start: float | None = None, end: float | None = None) -> ExperimentDataset:
    frame = dataset.frame
    mask = pd.Series(True, index=frame.index)
    if start is not None:
        mask &= frame[dataset.time_column] >= start
    if end is not None:
        mask &= frame[dataset.time_column] <= end
    return ExperimentDataset(name=dataset.name, frame=frame.loc[mask].reset_index(drop=True), time_column=dataset.time_column)


def residual_frame(project: Project, dataset: ExperimentDataset, mappings: tuple[DataMapping, ...]) -> pd.DataFrame:
    rows = []
    for _, data_row in dataset.frame.iterrows():
        time = float(data_row[dataset.time_column])
        outputs = _outputs_at_time(project, time)
        for mapping in mappings:
            observed = float(data_row[mapping.column])
            model = float(outputs.get(mapping.output, 0.0))
            residual = mapping.weight * (model - observed)
            rows.append(
                {
                    "experiment": dataset.name,
                    "time": time,
                    "output": mapping.output,
                    "observed": observed,
                    "model": model,
                    "weight": mapping.weight,
                    "residual": residual,
                }
            )
    return pd.DataFrame(rows)


def _outputs_at_time(project: Project, time: float) -> dict[str, float]:
    integration = project.recipe.integration
    recipe = Recipe(
        name=project.recipe.name,
        unit_system=project.recipe.unit_system,
        initial=project.recipe.initial,
        feed=project.recipe.feed,
        feed_tanks=list(project.recipe.feed_tanks),
        integration=IntegrationControl(
            t_final=time,
            output_points=max(2, min(integration.output_points, 12)),
            method=integration.method,
            rtol=integration.rtol,
            atol=integration.atol,
            backend=integration.backend,
            galerkin_cells=integration.galerkin_cells,
            galerkin_degree=integration.galerkin_degree,
        ),
        pre_schedule=list(project.recipe.pre_schedule),
        temperature_profile=list(project.recipe.temperature_profile),
        pressure_profile=list(project.recipe.pressure_profile),
        shooting_control=dict(project.recipe.shooting_control),
    )
    case = Project(
        schema_version=project.schema_version,
        name=project.name,
        reactor=project.reactor,
        kinetics=project.kinetics,
        recipe=recipe,
        outputs=project.outputs,
        heat_balance=project.heat_balance,
        substances=list(project.substances),
        polymers=list(project.polymers),
        reaction_steps=list(project.reaction_steps),
        generic_parameters=dict(project.generic_parameters),
    )
    return compute_generic_outputs(SimulationEngine(case).run(), case.outputs)
