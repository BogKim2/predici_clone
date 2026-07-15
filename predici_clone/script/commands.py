from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScriptCommandState:
    current_concentrations: dict[str, float] = field(default_factory=dict)
    initial_concentrations: dict[str, float] = field(default_factory=dict)
    final_concentrations: dict[str, float] = field(default_factory=dict)
    moments: dict[str, float] = field(default_factory=dict)
    parameters: dict[str, float] = field(default_factory=dict)
    variables: dict[str, float] = field(default_factory=dict)


def script_command_namespace(state: ScriptCommandState) -> dict[str, object]:
    def getx(name: str) -> float:
        return float(state.variables.get(name, state.current_concentrations.get(name, 0.0)))

    def getco(species: str) -> float:
        return float(state.current_concentrations.get(species, 0.0))

    def getcoini(species: str) -> float:
        return float(state.initial_concentrations.get(species, 0.0))

    def getconsum(species: str) -> float:
        return getcoini(species) - getco(species)

    def getcf(species: str) -> float:
        return float(state.final_concentrations.get(species, getco(species)))

    def getmy(moment: str) -> float:
        return float(state.moments.get(moment, 0.0))

    def gettotalmy() -> float:
        return float(state.moments.get("mass", state.moments.get("M0", 0.0)))

    def getkp(parameter: str) -> float:
        return float(state.parameters.get(parameter, 0.0))

    def setkp(parameter: str, value: float) -> float:
        state.parameters[parameter] = float(value)
        return float(value)

    namespace: dict[str, object] = {
        **state.variables,
        "getx": getx,
        "getco": getco,
        "getcoini": getcoini,
        "getconsum": getconsum,
        "getcf": getcf,
        "getmy": getmy,
        "gettotalmy": gettotalmy,
        "getkp": getkp,
        "setkp": setkp,
    }
    return namespace
