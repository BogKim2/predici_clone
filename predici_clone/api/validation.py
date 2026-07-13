from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from predici_clone.api.project_schema import Project


Severity = Literal["error", "warning"]


@dataclass(frozen=True)
class ValidationMessage:
    severity: Severity
    path: str
    code: str
    message: str


def validate_project(project: Project) -> list[ValidationMessage]:
    messages: list[ValidationMessage] = []
    _check_positive(messages, "reactor.nmax", project.reactor.nmax, "nmax_positive")
    _check_positive(messages, "reactor.volume", project.reactor.volume, "volume_positive")
    _check_positive(messages, "reactor.residence_time", project.reactor.residence_time, "residence_time_positive")
    _check_positive(messages, "reactor.stages", project.reactor.stages, "stages_positive")
    _check_positive(messages, "reactor.axial_cells", project.reactor.axial_cells, "axial_cells_positive")
    _check_positive(messages, "recipe.integration.t_final", project.recipe.integration.t_final, "t_final_positive")
    _check_positive(messages, "recipe.integration.output_points", project.recipe.integration.output_points, "output_points_positive")
    _check_positive(messages, "recipe.integration.galerkin_cells", project.recipe.integration.galerkin_cells, "galerkin_cells_positive")
    _check_non_negative(messages, "recipe.integration.galerkin_degree", project.recipe.integration.galerkin_degree, "galerkin_degree_non_negative")
    _check_non_negative(messages, "recipe.feed.rate", project.recipe.feed.rate, "feed_rate_non_negative")
    for index, tank in enumerate(project.recipe.feed_tanks):
        _check_non_negative(messages, f"recipe.feed_tanks[{index}].rate", tank.rate, "feed_tank_rate_non_negative")
    _check_non_negative(messages, "kinetics.kp", project.kinetics.kp, "kp_non_negative")
    _check_non_negative(messages, "kinetics.kt", project.kinetics.kt, "kt_non_negative")
    _check_non_negative(messages, "kinetics.kd", project.kinetics.kd, "kd_non_negative")

    backend = project.recipe.integration.backend
    if backend not in {"discrete", "galerkin", "galerkin_direct"}:
        messages.append(ValidationMessage("error", "recipe.integration.backend", "backend_supported", f"Unsupported backend: {backend}"))

    _check_profile(messages, "recipe.temperature_profile", project.recipe.temperature_profile)
    _check_profile(messages, "recipe.pressure_profile", project.recipe.pressure_profile)
    for index, step in enumerate(project.recipe.pre_schedule):
        action = step.get("action")
        path = f"recipe.pre_schedule[{index}]"
        if action not in {"set_feed_rate", "set_temperature", "set_pressure", "set_residence_time", "set_coolant_temperature", "set_additional_heat"}:
            messages.append(ValidationMessage("warning", path, "schedule_action_known", f"Unsupported schedule action: {action}"))
        if action == "set_feed_rate" and float(step.get("rate", 0.0)) < 0:
            messages.append(ValidationMessage("error", f"{path}.rate", "schedule_rate_non_negative", "Scheduled feed rate must be non-negative"))
        if action == "set_temperature" and not any(key in step for key in ("value", "temperature")):
            messages.append(ValidationMessage("error", path, "schedule_temperature_value_required", "Scheduled temperature requires value or temperature"))
        if action == "set_pressure":
            if not any(key in step for key in ("value", "pressure")):
                messages.append(ValidationMessage("error", path, "schedule_pressure_value_required", "Scheduled pressure requires value or pressure"))
            elif float(step.get("value", step.get("pressure", 0.0))) < 0:
                messages.append(ValidationMessage("error", path, "schedule_pressure_non_negative", "Scheduled pressure must be non-negative"))
        if action == "set_residence_time":
            if not any(key in step for key in ("value", "residence_time")):
                messages.append(ValidationMessage("error", path, "schedule_residence_time_value_required", "Scheduled residence time requires value or residence_time"))
            elif float(step.get("value", step.get("residence_time", 0.0))) <= 0:
                messages.append(ValidationMessage("error", path, "schedule_residence_time_positive", "Scheduled residence time must be positive"))
        if action == "set_coolant_temperature" and not any(key in step for key in ("value", "coolant_temperature", "temperature")):
            messages.append(ValidationMessage("error", path, "schedule_coolant_temperature_value_required", "Scheduled coolant temperature requires value, coolant_temperature, or temperature"))
        if action == "set_additional_heat" and not any(key in step for key in ("value", "heat", "additional_heat")):
            messages.append(ValidationMessage("error", path, "schedule_additional_heat_value_required", "Scheduled additional heat requires value, heat, or additional_heat"))

    if project.heat_balance.enabled:
        heat = project.heat_balance
        _check_non_negative(messages, "heat_balance.heat_transfer", heat.heat_transfer, "heat_transfer_non_negative")
        _check_non_negative(messages, "heat_balance.area", heat.area, "heat_area_non_negative")
        _check_non_negative(messages, "heat_balance.heat_capacity", heat.heat_capacity, "heat_capacity_non_negative")
        _check_non_negative(messages, "heat_balance.mass_flow", heat.mass_flow, "mass_flow_non_negative")
        _check_non_negative(messages, "heat_balance.mass_holdup", heat.mass_holdup, "mass_holdup_non_negative")
        if heat.use_heat_exchanger and (heat.heat_transfer == 0 or heat.area == 0):
            messages.append(ValidationMessage("warning", "heat_balance", "inactive_heat_exchanger", "Heat exchanger is enabled but UA is zero"))

    for index, step in enumerate(project.reaction_steps):
        for parameter in step.rate_law.parameters:
            if parameter not in project.generic_parameters:
                messages.append(
                    ValidationMessage(
                        "warning",
                        f"reaction_steps[{index}].rate_law.parameters",
                        "missing_generic_parameter",
                        f"Generic parameter {parameter} is not defined",
                    )
                )
    return messages


def validation_summary(messages: list[ValidationMessage]) -> dict[str, int]:
    return {
        "errors": sum(1 for message in messages if message.severity == "error"),
        "warnings": sum(1 for message in messages if message.severity == "warning"),
    }


def _check_positive(messages: list[ValidationMessage], path: str, value: float, code: str) -> None:
    if value <= 0:
        messages.append(ValidationMessage("error", path, code, f"{path} must be positive"))


def _check_non_negative(messages: list[ValidationMessage], path: str, value: float, code: str) -> None:
    if value < 0:
        messages.append(ValidationMessage("error", path, code, f"{path} must be non-negative"))


def _check_profile(messages: list[ValidationMessage], path: str, profile) -> None:
    previous_time = None
    for index, point in enumerate(profile):
        if point.time < 0:
            messages.append(ValidationMessage("error", f"{path}[{index}].time", "profile_time_non_negative", "Profile time must be non-negative"))
        if previous_time is not None and point.time <= previous_time:
            messages.append(ValidationMessage("error", path, "profile_time_increasing", "Profile times must be strictly increasing"))
        previous_time = point.time
