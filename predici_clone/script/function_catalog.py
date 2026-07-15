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
    base = (
        ScriptFunctionSpec("getx", ("name",), "substance", "Return the current scalar value for a named variable or species."),
        ScriptFunctionSpec("getco", ("species",), "substance", "Return the current concentration of a species."),
        ScriptFunctionSpec("getcoini", ("species",), "substance", "Return the initial concentration of a species."),
        ScriptFunctionSpec("getconsum", ("species",), "substance", "Return initial minus current concentration."),
        ScriptFunctionSpec("getcf", ("species",), "substance", "Return the final concentration of a species."),
        ScriptFunctionSpec("getmy", ("moment",), "distribution", "Return a named distribution moment such as Mn or Mw."),
        ScriptFunctionSpec("weightedmy", ("moment", "weight"), "distribution", "Return a supplied weighted moment or apply a moment weight factor."),
        ScriptFunctionSpec("gettotalmy", (), "distribution", "Return the total distribution mass moment."),
        ScriptFunctionSpec("getkp", ("parameter",), "parameter", "Return a kinetic parameter value."),
        ScriptFunctionSpec("getkpreac", ("parameter", "reaction"), "parameter", "Return a reaction-specific kinetic parameter value."),
        ScriptFunctionSpec("setkp", ("parameter", "value"), "parameter", "Set a kinetic parameter in the local script command state."),
        ScriptFunctionSpec("addvalue", ("name", "value"), "output", "Accumulate a named local output value."),
        ScriptFunctionSpec("getuxr", ("reactor", "position"), "reactor", "Return or interpolate a reactor profile value."),
        ScriptFunctionSpec("getkpt", ("parameter", "time"), "parameter", "Return or interpolate a time-dependent parameter value."),
        ScriptFunctionSpec("getkptp", ("parameter", "time", "position"), "parameter", "Return or interpolate a time/position parameter value."),
    )
    extended = (
        ("getmn", (), "distribution"), ("getmw", (), "distribution"), ("getmz", (), "distribution"),
        ("getmolpart", ("name",), "substance"), ("getmasspart", ("name",), "substance"),
        ("getfeedmass", ("name",), "reactor"), ("getfeedmol", ("name",), "reactor"),
        ("gettankmass", ("name",), "reactor"), ("gettankmol", ("name",), "reactor"),
        ("getphasemass", ("phase",), "reactor"), ("getdensity", (), "reactor"),
        ("getmass", (), "reactor"), ("getpressure", (), "reactor"), ("gettemp", (), "reactor"),
        ("copyreactor", ("src", "dst", "factor"), "reactor"), ("findroot", ("function", "initial"), "math"),
        ("getprofmy", ("name", "moment"), "distribution"), ("getmcinfo", ("name", "type"), "montecarlo"),
        ("getmcaverage", ("name", "length", "index", "interpolated"), "montecarlo"),
        ("co_action", ("action",), "cape-open"), ("co_attribute", ("compound", "property", "temperature"), "cape-open"),
        ("co_get", ("info", "phase", "compound"), "cape-open"), ("co_set", ("info", "phase", "compound", "value"), "cape-open"),
        ("dbpar", ("set", "property", "unit"), "database"), ("dbfunc", ("set", "property", "temperature", "unit"), "database"),
        ("WriteMCDist", ("path",), "montecarlo"),
    )
    return (*base, *(ScriptFunctionSpec(name, arguments, category, f"PREDICI-compatible {name} command.") for name, arguments, category in extended))
