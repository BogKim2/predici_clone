from __future__ import annotations

from pathlib import Path
from typing import Any

from predici_clone.api.automation import (
    get_dist_moments,
    get_dist_points,
    get_reactor_pressure,
    set_dist_lumping,
    set_enthalpy,
    set_feed_rate,
    set_heat_exchanger,
)
from predici_clone.api.project_schema import Project
from predici_clone.engine.simulation_result import SimulationResult


def export_matlab_moment_equations(project: Project, path: str | Path | None = None) -> str:
    text = _moment_equation_text(project, language="matlab")
    if path is not None:
        Path(path).write_text(text, encoding="utf-8")
    return text


def export_c_moment_equations(project: Project, path: str | Path | None = None) -> str:
    text = _moment_equation_text(project, language="c")
    if path is not None:
        Path(path).write_text(text, encoding="utf-8")
    return text


def execute_public_command(
    command: str,
    *,
    project: Project | None = None,
    result: SimulationResult | None = None,
    **kwargs: Any,
) -> Any:
    commands = {
        "GetDistPoints": lambda: get_dist_points(_require_result(result), **kwargs),
        "GetDistMoments": lambda: get_dist_moments(_require_result(result)),
        "GetReactorPressure": lambda: get_reactor_pressure(_require_result(result), kwargs.get("reactor_name", "default")),
        "SetFeedRate": lambda: set_feed_rate(_require_project(project), float(kwargs["rate"])),
        "SetDistLumping": lambda: set_dist_lumping(_require_project(project), bool(kwargs["on_off"])),
        "SetEnthalpy": lambda: set_enthalpy(
            _require_project(project),
            str(kwargs.get("step_type", "")),
            str(kwargs.get("reactant", "")),
            float(kwargs["value"]),
        ),
        "SetHeatExchanger": lambda: set_heat_exchanger(_require_project(project), **kwargs),
    }
    try:
        return commands[command]()
    except KeyError as exc:
        raise ValueError(f"Unsupported public command: {command}") from exc


def _moment_equation_text(project: Project, *, language: str) -> str:
    kp = float(project.generic_parameters.get("GP_kp", project.kinetics.kp))
    kt = float(project.generic_parameters.get("GP_kt", project.kinetics.kt))
    kd = float(project.generic_parameters.get("GP_kd", project.kinetics.kd))
    efficiency = float(project.kinetics.initiator_efficiency)
    if language == "matlab":
        return "\n".join(
            [
                "function dydt = predici_moments(t, y)",
                f"kp = {kp:.17g}; kt = {kt:.17g}; kd = {kd:.17g}; f = {efficiency:.17g};",
                "% y = [M; I; R; M0; M1; M2; M3]",
                "M = y(1); I = y(2); R = y(3); M0 = y(4); M1 = y(5); M2 = y(6); M3 = y(7);",
                "dM = -kp * M * R;",
                "dI = -kd * I;",
                "dR = 2 * f * kd * I - kt * R * R;",
                "dM0 = kp * M * R;",
                "dM1 = kp * M * (M0 + R);",
                "dM2 = kp * M * (2 * M1 + M0 + R);",
                "dM3 = kp * M * (3 * M2 + 3 * M1 + M0 + R);",
                "dydt = [dM; dI; dR; dM0; dM1; dM2; dM3];",
                "end",
            ]
        )
    if language == "c":
        return "\n".join(
            [
                "void predici_moments(double t, const double y[7], double dydt[7]) {",
                f"  const double kp = {kp:.17g}, kt = {kt:.17g}, kd = {kd:.17g}, f = {efficiency:.17g};",
                "  const double M = y[0], I = y[1], R = y[2], M0 = y[3], M1 = y[4], M2 = y[5];",
                "  (void)t;",
                "  dydt[0] = -kp * M * R;",
                "  dydt[1] = -kd * I;",
                "  dydt[2] = 2.0 * f * kd * I - kt * R * R;",
                "  dydt[3] = kp * M * R;",
                "  dydt[4] = kp * M * (M0 + R);",
                "  dydt[5] = kp * M * (2.0 * M1 + M0 + R);",
                "  dydt[6] = kp * M * (3.0 * M2 + 3.0 * M1 + M0 + R);",
                "}",
            ]
        )
    raise ValueError(f"Unsupported export language: {language}")


def _require_project(project: Project | None) -> Project:
    if project is None:
        raise ValueError("project is required")
    return project


def _require_result(result: SimulationResult | None) -> SimulationResult:
    if result is None:
        raise ValueError("result is required")
    return result
