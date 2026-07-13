from __future__ import annotations

import numpy as np

from predici_clone.api.project_schema import FeedStream, HeatBalanceConfig, Project, Recipe
from predici_clone.engine.simulation_result import SimulationResult


def create_recipe(project: Project, recipe_name: str, option: str = "copy") -> Project:
    recipe = Recipe(
        name=recipe_name,
        unit_system=project.recipe.unit_system,
        initial=project.recipe.initial,
        feed=project.recipe.feed,
        feed_tanks=list(project.recipe.feed_tanks),
        polymer_feed=list(project.recipe.polymer_feed),
        integration=project.recipe.integration,
        pre_schedule=list(project.recipe.pre_schedule),
        temperature_profile=list(project.recipe.temperature_profile),
        pressure_profile=list(project.recipe.pressure_profile),
        shooting_control={"option": option, **project.recipe.shooting_control},
    )
    return Project(
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


def set_feed_rate(project: Project, rate: float) -> Project:
    feed = FeedStream(
        monomer=project.recipe.feed.monomer,
        initiator=project.recipe.feed.initiator,
        radicals=project.recipe.feed.radicals,
        rate=rate,
    )
    recipe = Recipe(
        name=project.recipe.name,
        unit_system=project.recipe.unit_system,
        initial=project.recipe.initial,
        feed=feed,
        feed_tanks=list(project.recipe.feed_tanks),
        polymer_feed=list(project.recipe.polymer_feed),
        integration=project.recipe.integration,
        pre_schedule=list(project.recipe.pre_schedule),
        temperature_profile=list(project.recipe.temperature_profile),
        pressure_profile=list(project.recipe.pressure_profile),
        shooting_control=dict(project.recipe.shooting_control),
    )
    return Project(
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


def get_dist_points(
    result: SimulationResult,
    *,
    normed_output: bool = True,
    graphic_weight: bool = True,
    log_axis: bool = False,
    x_as_mol_weight: bool = False,
) -> np.ndarray:
    lengths = np.arange(result.first_length, result.first_length + result.final_distribution.size, dtype=float)
    x = lengths.copy()
    if x_as_mol_weight:
        x = x
    y = result.final_distribution.copy()
    if graphic_weight:
        y = y * lengths
    if normed_output and np.sum(y) > 0:
        y = y / np.sum(y)
    if log_axis:
        x = np.log10(np.maximum(x, 1e-12))
    return np.column_stack([x, y])


def get_dist_moments(result: SimulationResult) -> dict[str, float]:
    report = result.final_moments
    return {
        "M0": report.m0,
        "M1": report.m1,
        "M2": report.m2,
        "M3": report.m3,
        "Mn": report.mn,
        "Mw": report.mw,
        "Mz": report.mz,
        "PDI": report.pdi,
        "AMW": report.amw,
        "mass": report.mass,
    }


def set_dist_lumping(project: Project, on_off: bool) -> Project:
    parameters = dict(project.generic_parameters)
    parameters["dist_lumping"] = float(bool(on_off))
    return Project(
        schema_version=project.schema_version,
        name=project.name,
        reactor=project.reactor,
        kinetics=project.kinetics,
        recipe=project.recipe,
        outputs=project.outputs,
        heat_balance=project.heat_balance,
        substances=list(project.substances),
        polymers=list(project.polymers),
        reaction_steps=list(project.reaction_steps),
        generic_parameters=parameters,
    )


def get_reactor_pressure(result: SimulationResult, _reactor_name: str = "default") -> float:
    return float(result.metadata.get("final_pressure", 1.0))


def set_heat_exchanger(
    project: Project,
    *,
    use_heat_exchanger: bool,
    heat_transfer: float,
    area: float,
    heat_capacity: float,
    mass_flow: float,
    mass_holdup: float,
    initial_feed_temp: float,
    coolant_temperature: float | None = None,
    additional_heat: float = 0.0,
    counter_current: bool = False,
) -> Project:
    heat_balance = HeatBalanceConfig(
        enabled=True,
        use_heat_exchanger=use_heat_exchanger,
        heat_transfer=heat_transfer,
        area=area,
        heat_capacity=heat_capacity,
        mass_flow=mass_flow,
        mass_holdup=mass_holdup,
        initial_feed_temp=initial_feed_temp,
        coolant_temperature=initial_feed_temp if coolant_temperature is None else coolant_temperature,
        additional_heat=additional_heat,
        counter_current=counter_current,
    )
    return Project(
        schema_version=project.schema_version,
        name=project.name,
        reactor=project.reactor,
        kinetics=project.kinetics,
        recipe=project.recipe,
        outputs=project.outputs,
        heat_balance=heat_balance,
        substances=list(project.substances),
        polymers=list(project.polymers),
        reaction_steps=list(project.reaction_steps),
        generic_parameters=dict(project.generic_parameters),
    )


def check_enthalpy(project: Project, _reactor_name: str = "default") -> bool:
    if not project.heat_balance.enabled:
        return True
    heat = project.heat_balance
    return heat.heat_capacity >= 0 and heat.mass_flow >= 0 and heat.mass_holdup >= 0


def set_enthalpy(project: Project, step_type: str, reactant: str, value: float) -> Project:
    parameters = dict(project.generic_parameters)
    parameters["reaction_enthalpy"] = float(value)
    if step_type or reactant:
        parameters[f"enthalpy:{step_type}:{reactant}"] = float(value)
    heat_balance = HeatBalanceConfig(
        enabled=True,
        use_heat_exchanger=project.heat_balance.use_heat_exchanger,
        heat_transfer=project.heat_balance.heat_transfer,
        area=project.heat_balance.area,
        heat_capacity=project.heat_balance.heat_capacity,
        mass_flow=project.heat_balance.mass_flow,
        mass_holdup=project.heat_balance.mass_holdup,
        initial_feed_temp=project.heat_balance.initial_feed_temp,
        coolant_temperature=project.heat_balance.coolant_temperature,
        additional_heat=project.heat_balance.additional_heat,
        counter_current=project.heat_balance.counter_current,
    )
    return Project(
        schema_version=project.schema_version,
        name=project.name,
        reactor=project.reactor,
        kinetics=project.kinetics,
        recipe=project.recipe,
        outputs=project.outputs,
        heat_balance=heat_balance,
        substances=list(project.substances),
        polymers=list(project.polymers),
        reaction_steps=list(project.reaction_steps),
        generic_parameters=parameters,
    )


def activate_detailed_iteration(
    project: Project,
    *,
    target_output: str,
    target_value: float,
    tune_parameter: str,
    initial: float,
    lower: float,
    upper: float,
    weight: float = 1.0,
):
    from predici_clone.engine.shooting import ShootingControl, activate_detailed_iteration as _activate_detailed_iteration

    return _activate_detailed_iteration(
        project,
        ShootingControl(
            target_output=target_output,
            target_value=target_value,
            tune_parameter=tune_parameter,
            initial=initial,
            lower=lower,
            upper=upper,
            weight=weight,
        ),
    )
