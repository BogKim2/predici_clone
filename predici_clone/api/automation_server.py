from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from predici_clone.api.interoperability import execute_public_command
from predici_clone.api.project_io import load_project, save_project
from predici_clone.api.project_schema import Project
from predici_clone.engine import SimulationEngine
from predici_clone.engine.simulation_result import SimulationResult
from predici_clone.montecarlo.ensemble import ChainEnsemble


@dataclass
class AutomationServer:
    project: Project | None = None
    result: SimulationResult | None = None

    def new(self) -> Project:
        self.project = Project()
        self.result = None
        return self.project

    def load(self, path: str | Path) -> Project:
        self.project = load_project(path)
        self.result = None
        return self.project

    def save(self, path: str | Path) -> Path:
        if self.project is None:
            raise ValueError("no project loaded")
        save_project(self.project, path)
        return Path(path)

    def set_parameter(self, name: str, value: float) -> None:
        if self.project is None:
            raise ValueError("no project loaded")
        self.project.generic_parameters[name] = float(value)

    def run(self) -> SimulationResult:
        if self.project is None:
            raise ValueError("no project loaded")
        self.result = SimulationEngine(self.project).run()
        return self.result

    def command(self, name: str, **kwargs):
        return execute_public_command(name, project=self.project, result=self.result, **kwargs)

    def activate_qbasic_iteration(self, heat_script, initial_temperature: float) -> float:
        return float(heat_script(float(initial_temperature)))

    def write_mc_dist(self, ensemble: ChainEnsemble, path: str | Path) -> Path:
        destination = Path(path)
        ensemble.save(destination)
        return destination

    def get_parameter(self, name: str) -> float:
        if self.project is None:
            raise ValueError("no project loaded")
        return float(self.project.generic_parameters.get(name, 0.0))

    def get_result_value(self, name: str) -> float:
        if self.result is None:
            raise ValueError("no simulation result")
        moments = self.result.final_moments
        values = {"Mn": moments.mn, "Mw": moments.mw, "Mz": moments.mz, "PDI": moments.pdi, "mass": moments.mass}
        if name not in values:
            raise ValueError(f"Unknown result value: {name}")
        return float(values[name])

    @property
    def available_commands(self) -> tuple[str, ...]:
        return (
            "New", "Load", "Save", "Run", "SetParameter", "GetParameter", "GetResultValue",
            "CreateRecipe", "GetDistPoints", "GetDistMoments", "ExportResultNPZ", "GetReactorPressure",
            "CheckEnthalpy", "SetFeedRate", "SetDistLumping", "SetEnthalpy", "SetHeatExchanger",
            "ActivateDetailedIteration", "ActivateQBasicIteration", "WriteMCDist",
        )
