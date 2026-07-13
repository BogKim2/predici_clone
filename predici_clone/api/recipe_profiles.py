from __future__ import annotations

from dataclasses import replace
from typing import Any

import numpy as np

from predici_clone.api.project_schema import FeedStream, ProfilePoint, Project, ReactorConfig, Recipe


def evaluate_profile(profile: list[ProfilePoint] | tuple[ProfilePoint, ...], time: float, default: float) -> float:
    if not profile:
        return float(default)
    points = sorted(profile, key=lambda point: point.time)
    times = np.asarray([point.time for point in points], dtype=float)
    values = np.asarray([point.value for point in points], dtype=float)
    return float(np.interp(float(time), times, values, left=values[0], right=values[-1]))


def set_temperature_profile(project: Project, points: list[tuple[float, float]] | tuple[tuple[float, float], ...]) -> Project:
    return _with_recipe(project, replace(project.recipe, temperature_profile=_profile(points)))


def set_pressure_profile(project: Project, points: list[tuple[float, float]] | tuple[tuple[float, float], ...]) -> Project:
    return _with_recipe(project, replace(project.recipe, pressure_profile=_profile(points)))


def add_feed_tank(project: Project, *, monomer: float, initiator: float, radicals: float = 0.0, rate: float = 0.0) -> Project:
    tanks = [*project.recipe.feed_tanks, FeedStream(monomer=monomer, initiator=initiator, radicals=radicals, rate=rate)]
    return _with_recipe(project, replace(project.recipe, feed_tanks=tanks))


def effective_feed_stream(recipe: Recipe) -> FeedStream:
    tanks = [recipe.feed, *recipe.feed_tanks]
    total_rate = float(sum(max(tank.rate, 0.0) for tank in tanks))
    if total_rate <= 0:
        return FeedStream(
            monomer=recipe.feed.monomer,
            initiator=recipe.feed.initiator,
            radicals=recipe.feed.radicals,
            rate=0.0,
        )
    return FeedStream(
        monomer=sum(max(tank.rate, 0.0) * tank.monomer for tank in tanks) / total_rate,
        initiator=sum(max(tank.rate, 0.0) * tank.initiator for tank in tanks) / total_rate,
        radicals=sum(max(tank.rate, 0.0) * tank.radicals for tank in tanks) / total_rate,
        rate=total_rate,
    )


def append_pre_schedule_step(project: Project, time: float, action: str, **values: Any) -> Project:
    schedule = list(project.recipe.pre_schedule)
    schedule.append({"time": float(time), "action": action, **values})
    schedule.sort(key=lambda item: float(item.get("time", 0.0)))
    return _with_recipe(project, replace(project.recipe, pre_schedule=schedule))


def apply_pre_schedule(project: Project, time: float) -> Project:
    recipe = project.recipe
    feed = recipe.feed
    reactor = project.reactor
    for step in recipe.pre_schedule:
        if float(step.get("time", 0.0)) > time:
            continue
        action = step.get("action")
        if action == "set_feed_rate":
            feed = FeedStream(
                monomer=feed.monomer,
                initiator=feed.initiator,
                radicals=feed.radicals,
                rate=float(step.get("rate", feed.rate)),
            )
        if action == "set_residence_time":
            reactor = replace(reactor, residence_time=float(step.get("value", step.get("residence_time", reactor.residence_time))))
    return _with_recipe_and_reactor(project, replace(recipe, feed=feed), reactor)


def scheduled_feed_rate(recipe: Recipe, time: float) -> float:
    rate = float(effective_feed_stream(recipe).rate)
    for step in sorted(recipe.pre_schedule, key=lambda item: float(item.get("time", 0.0))):
        if float(step.get("time", 0.0)) > time:
            break
        if step.get("action") == "set_feed_rate":
            rate = float(step.get("rate", rate))
    return rate


def scheduled_temperature(recipe: Recipe, time: float, default: float) -> float:
    value = evaluate_profile(recipe.temperature_profile, time, default)
    return _scheduled_value(recipe, time, "set_temperature", value, ("value", "temperature"))


def scheduled_pressure(recipe: Recipe, time: float, default: float = 1.0) -> float:
    value = evaluate_profile(recipe.pressure_profile, time, default)
    return _scheduled_value(recipe, time, "set_pressure", value, ("value", "pressure"))


def scheduled_residence_time(recipe: Recipe, time: float, default: float) -> float:
    return _scheduled_value(recipe, time, "set_residence_time", default, ("value", "residence_time"))


def scheduled_coolant_temperature(recipe: Recipe, time: float, default: float) -> float:
    return _scheduled_value(recipe, time, "set_coolant_temperature", default, ("value", "coolant_temperature", "temperature"))


def scheduled_additional_heat(recipe: Recipe, time: float, default: float) -> float:
    return _scheduled_value(recipe, time, "set_additional_heat", default, ("value", "heat", "additional_heat"))


def _scheduled_value(recipe: Recipe, time: float, action: str, default: float, keys: tuple[str, ...]) -> float:
    value = float(default)
    for step in sorted(recipe.pre_schedule, key=lambda item: float(item.get("time", 0.0))):
        if float(step.get("time", 0.0)) > time:
            break
        if step.get("action") != action:
            continue
        for key in keys:
            if key in step:
                value = float(step[key])
                break
    return value


def _profile(points: list[tuple[float, float]] | tuple[tuple[float, float], ...]) -> list[ProfilePoint]:
    return [ProfilePoint(float(time), float(value)) for time, value in sorted(points)]


def _with_recipe(project: Project, recipe: Recipe) -> Project:
    return _with_recipe_and_reactor(project, recipe, project.reactor)


def _with_recipe_and_reactor(project: Project, recipe: Recipe, reactor: ReactorConfig) -> Project:
    return Project(
        schema_version=project.schema_version,
        name=project.name,
        reactor=reactor,
        kinetics=project.kinetics,
        recipe=recipe,
        outputs=project.outputs,
        heat_balance=project.heat_balance,
        substances=list(project.substances),
        polymers=list(project.polymers),
        reaction_steps=list(project.reaction_steps),
        generic_parameters=dict(project.generic_parameters),
    )
