from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from predici_clone.api.project_schema import Project
from predici_clone.thermo.flash import FlashResult, pt_flash
from predici_clone.thermo.peng_robinson import PengRobinsonEOS


@dataclass(frozen=True)
class CapeOpenCapability:
    component_name: str
    version: str
    supported_reactors: tuple[str, ...]
    supported_operations: tuple[str, ...]
    supports_dynamic_simulation: bool
    supports_parameter_estimation: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def cape_open_capability(project: Project | None = None) -> CapeOpenCapability:
    reactors = ("Batch", "Semi-batch", "CSTR", "Cascade", "PFR")
    if project is not None:
        reactors = tuple(kind for kind in reactors if kind == project.reactor.kind) or reactors
    return CapeOpenCapability(
        component_name="PrediciClone",
        version="2.0",
        supported_reactors=reactors,
        supported_operations=(
            "material_balance",
            "energy_balance",
            "distribution_moments",
            "parameter_estimation",
            "public_command_dispatch",
            "peng_robinson_fugacity",
            "pt_flash",
            "mixture_density",
        ),
        supports_dynamic_simulation=True,
        supports_parameter_estimation=True,
        notes="In-process Peng-Robinson property package; this is not a COM registration, and optional COM wrapping remains adapter-specific.",
    )


def cape_open_manifest(project: Project | None = None) -> dict[str, Any]:
    capability = cape_open_capability(project)
    return {
        "cape_open": capability.to_dict(),
        "interfaces": {
            "material_object": "distribution_history, state_history, metadata",
            "unit_operation": "SimulationEngine.run",
            "parameters": "Project.generic_parameters",
        },
    }


def cape_open_pt_flash(
    eos: PengRobinsonEOS,
    temperature: float,
    pressure: float,
    composition,
) -> FlashResult:
    return pt_flash(eos, temperature, pressure, composition)
