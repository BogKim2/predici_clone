from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScriptCommandState:
    current_concentrations: dict[str, float] = field(default_factory=dict)
    initial_concentrations: dict[str, float] = field(default_factory=dict)
    final_concentrations: dict[str, float] = field(default_factory=dict)
    moments: dict[str, float] = field(default_factory=dict)
    weighted_moments: dict[str, float] = field(default_factory=dict)
    parameters: dict[str, float] = field(default_factory=dict)
    reaction_parameters: dict[str, float] = field(default_factory=dict)
    time_parameters: dict[tuple[str, float], float] = field(default_factory=dict)
    time_position_parameters: dict[tuple[str, float, float], float] = field(default_factory=dict)
    reactor_values: dict[str, float] = field(default_factory=dict)
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

    def weightedmy(moment: str) -> float:
        return float(state.weighted_moments.get(moment, getmy(moment)))

    def gettotalmy() -> float:
        return float(state.moments.get("mass", state.moments.get("M0", 0.0)))

    def getkp(parameter: str) -> float:
        return float(state.parameters.get(parameter, 0.0))

    def getkpreac(parameter: str, reaction: str = "") -> float:
        key = f"{reaction}:{parameter}" if reaction else parameter
        return float(state.reaction_parameters.get(key, getkp(parameter)))

    def setkp(parameter: str, value: float) -> float:
        state.parameters[parameter] = float(value)
        return float(value)

    def getkpt(parameter: str, time: float) -> float:
        return float(state.time_parameters.get((parameter, float(time)), getkp(parameter)))

    def getkptp(parameter: str, time: float, position: float) -> float:
        key = (parameter, float(time), float(position))
        return float(state.time_position_parameters.get(key, getkpt(parameter, time)))

    def getuxr(reactor: str) -> float:
        return float(state.reactor_values.get(reactor, 0.0))

    def addvalue(name: str, value: float) -> float:
        state.variables[name] = float(state.variables.get(name, 0.0)) + float(value)
        return state.variables[name]

    namespace: dict[str, object] = {
        **state.variables,
        "getx": getx,
        "getco": getco,
        "getcoini": getcoini,
        "getconsum": getconsum,
        "getcf": getcf,
        "getmy": getmy,
        "weightedmy": weightedmy,
        "gettotalmy": gettotalmy,
        "getkp": getkp,
        "getkpreac": getkpreac,
        "setkp": setkp,
        "getkpt": getkpt,
        "getkptp": getkptp,
        "getuxr": getuxr,
        "addvalue": addvalue,
    }
    return namespace
