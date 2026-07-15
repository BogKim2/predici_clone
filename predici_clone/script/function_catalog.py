from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ScriptFunctionSpec:
    name: str
    arguments: tuple[str, ...]
    category: str
    description: str
    implemented: bool = True


def script_function_catalog() -> tuple[ScriptFunctionSpec, ...]:
    return (
        ScriptFunctionSpec("getx", ("name",), "substance", "Return the current scalar value for a named variable or species."),
        ScriptFunctionSpec("getco", ("species",), "substance", "Return the current concentration of a species."),
        ScriptFunctionSpec("getcoini", ("species",), "substance", "Return the initial concentration of a species."),
        ScriptFunctionSpec("getconsum", ("species",), "substance", "Return initial minus current concentration."),
        ScriptFunctionSpec("getcf", ("species",), "substance", "Return the final concentration of a species."),
        ScriptFunctionSpec("getmy", ("moment",), "distribution", "Return a named distribution moment such as Mn or Mw."),
        ScriptFunctionSpec("gettotalmy", (), "distribution", "Return the total distribution mass moment."),
        ScriptFunctionSpec("getkp", ("parameter",), "parameter", "Return a kinetic parameter value."),
        ScriptFunctionSpec("setkp", ("parameter", "value"), "parameter", "Set a kinetic parameter in the local script command state."),
        ScriptFunctionSpec("weightedmy", ("moment",), "distribution", "Weighted moment helper reserved for PDE workflows.", False),
        ScriptFunctionSpec("getuxr", ("reactor",), "reactor", "Reactor profile helper reserved for PDE workflows.", False),
        ScriptFunctionSpec("getkpt", ("parameter", "time"), "parameter", "Time-dependent parameter helper reserved for future workflows.", False),
        ScriptFunctionSpec("getkptp", ("parameter", "time", "position"), "parameter", "Time/position parameter helper reserved for future workflows.", False),
    )
