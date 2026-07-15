from __future__ import annotations

from dataclasses import dataclass, field
from scipy.optimize import newton


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
    parameter_profiles: dict[str, tuple[tuple[float, float], ...]] = field(default_factory=dict)
    parameter_surfaces: dict[str, tuple[tuple[float, float, float], ...]] = field(default_factory=dict)
    reactor_values: dict[str, float] = field(default_factory=dict)
    reactor_profiles: dict[str, tuple[tuple[float, float], ...]] = field(default_factory=dict)
    moment_weights: dict[str, float] = field(default_factory=dict)
    variables: dict[str, float] = field(default_factory=dict)
    molar_parts: dict[str, float] = field(default_factory=dict)
    mass_parts: dict[str, float] = field(default_factory=dict)
    feed_masses: dict[str, float] = field(default_factory=dict)
    feed_moles: dict[str, float] = field(default_factory=dict)
    tank_masses: dict[str, float] = field(default_factory=dict)
    tank_moles: dict[str, float] = field(default_factory=dict)
    phase_masses: dict[str, float] = field(default_factory=dict)
    reactor_states: dict[str, dict[str, float]] = field(default_factory=dict)
    profile_moments: dict[tuple[str, int], float] = field(default_factory=dict)
    external_functions: dict[str, object] = field(default_factory=dict)


def _linear_profile_value(points: tuple[tuple[float, float], ...], coordinate: float, default: float) -> float:
    if not points:
        return float(default)
    ordered = sorted((float(x), float(y)) for x, y in points)
    x = float(coordinate)
    if x <= ordered[0][0]:
        return ordered[0][1]
    if x >= ordered[-1][0]:
        return ordered[-1][1]
    for (x0, y0), (x1, y1) in zip(ordered, ordered[1:]):
        if x0 <= x <= x1:
            if x1 == x0:
                return y1
            fraction = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * fraction
    return float(default)


def _bracket(values: list[float], coordinate: float) -> tuple[float, float] | None:
    if len(values) < 2 or coordinate < values[0] or coordinate > values[-1]:
        return None
    for lower, upper in zip(values, values[1:]):
        if lower <= coordinate <= upper:
            return lower, upper
    return None


def _surface_profile_value(
    points: tuple[tuple[float, float, float], ...],
    time: float,
    position: float,
    default: float,
) -> float:
    if not points:
        return float(default)
    triples = [(float(t), float(p), float(v)) for t, p, v in points]
    t = float(time)
    p = float(position)
    for point_time, point_position, value in triples:
        if point_time == t and point_position == p:
            return value

    times = sorted({point_time for point_time, _, _ in triples})
    positions = sorted({point_position for _, point_position, _ in triples})
    time_bracket = _bracket(times, t)
    position_bracket = _bracket(positions, p)
    lookup = {(point_time, point_position): value for point_time, point_position, value in triples}
    if time_bracket and position_bracket:
        t0, t1 = time_bracket
        p0, p1 = position_bracket
        corners = ((t0, p0), (t1, p0), (t0, p1), (t1, p1))
        if all(corner in lookup for corner in corners):
            v00 = lookup[(t0, p0)]
            v10 = lookup[(t1, p0)]
            v01 = lookup[(t0, p1)]
            v11 = lookup[(t1, p1)]
            time_fraction = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            position_fraction = 0.0 if p1 == p0 else (p - p0) / (p1 - p0)
            lower = v00 + (v10 - v00) * time_fraction
            upper = v01 + (v11 - v01) * time_fraction
            return lower + (upper - lower) * position_fraction

    weighted_sum = 0.0
    weight_total = 0.0
    for point_time, point_position, value in triples:
        distance_squared = (point_time - t) ** 2 + (point_position - p) ** 2
        if distance_squared == 0.0:
            return value
        weight = 1.0 / distance_squared
        weighted_sum += value * weight
        weight_total += weight
    return weighted_sum / weight_total if weight_total else float(default)


def script_command_namespace(state: ScriptCommandState, procedures: dict[str, object] | None = None) -> dict[str, object]:
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

    def weightedmy(moment: str, weight: float = 1.0) -> float:
        if moment in state.weighted_moments:
            return float(state.weighted_moments[moment])
        factor = float(state.moment_weights.get(moment, weight))
        return getmy(moment) * factor

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
        exact_key = (parameter, float(time))
        if exact_key in state.time_parameters:
            return float(state.time_parameters[exact_key])
        return _linear_profile_value(state.parameter_profiles.get(parameter, ()), float(time), getkp(parameter))

    def getkptp(parameter: str, time: float, position: float) -> float:
        key = (parameter, float(time), float(position))
        if key in state.time_position_parameters:
            return float(state.time_position_parameters[key])
        return _surface_profile_value(
            state.parameter_surfaces.get(parameter, ()),
            float(time),
            float(position),
            getkpt(parameter, time),
        )

    def getuxr(reactor: str, position: float = 0.0) -> float:
        if reactor in state.reactor_values:
            return float(state.reactor_values[reactor])
        return _linear_profile_value(state.reactor_profiles.get(reactor, ()), float(position), 0.0)

    def addvalue(name: str, value: float) -> float:
        state.variables[name] = float(state.variables.get(name, 0.0)) + float(value)
        return state.variables[name]

    def copyreactor(source: str, target: str, factor: float = 1.0) -> float:
        state.reactor_states[target] = {name: float(value) * float(factor) for name, value in state.reactor_states.get(source, {}).items()}
        return float(sum(state.reactor_states[target].values()))

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
        "getmn": lambda: getmy("Mn"),
        "getmw": lambda: getmy("Mw"),
        "getmz": lambda: getmy("Mz"),
        "getmolpart": lambda name: float(state.molar_parts.get(name, 0.0)),
        "getmasspart": lambda name: float(state.mass_parts.get(name, 0.0)),
        "getfeedmass": lambda name: float(state.feed_masses.get(name, 0.0)),
        "getfeedmol": lambda name: float(state.feed_moles.get(name, 0.0)),
        "gettankmass": lambda name: float(state.tank_masses.get(name, 0.0)),
        "gettankmol": lambda name: float(state.tank_moles.get(name, 0.0)),
        "getphasemass": lambda phase: float(state.phase_masses.get(phase, 0.0)),
        "getdensity": lambda: float(state.variables.get("density", 0.0)),
        "getmass": lambda: float(state.variables.get("mass", 0.0)),
        "getpressure": lambda: float(state.variables.get("pressure", 0.0)),
        "gettemp": lambda: float(state.variables.get("temperature", 0.0)),
        "copyreactor": copyreactor,
        "findroot": lambda function, initial: float(newton(function, initial)),
        "getprofmy": lambda name, moment: float(state.profile_moments.get((name, int(moment)), 0.0)),
    }
    namespace.update(state.external_functions)
    if procedures:
        namespace.update(procedures)
    return namespace
