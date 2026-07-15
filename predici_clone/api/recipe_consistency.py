from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal


RecipeInputMode = Literal[
    "absolute_mass",
    "mass_part_total_mass",
    "absolute_mole",
    "mole_part",
    "concentration_and_volume",
    "mass_part_total_mole",
    "mole_part_total_mass",
]


@dataclass(frozen=True)
class RecipeComponent:
    name: str
    molecular_weight: float
    density: float
    mass: float = 0.0
    mass_part: float = 0.0
    moles: float = 0.0
    mole_part: float = 0.0
    concentration: float = 0.0


@dataclass(frozen=True)
class RecipeComposition:
    mode: RecipeInputMode
    components: tuple[RecipeComponent, ...]
    volume: float
    total_mass: float
    total_moles: float
    consistency_sum: float
    temperature: float | None = None
    pressure: float | None = None


def normalize_recipe_components(
    mode: RecipeInputMode,
    components: tuple[RecipeComponent, ...] | list[RecipeComponent],
    *,
    volume: float | None = None,
    total_mass: float | None = None,
    total_moles: float | None = None,
    temperature: float | None = None,
    pressure: float | None = None,
) -> RecipeComposition:
    rows = tuple(components)
    _require_positive_thermo(rows)
    mode = _normalize_mode(mode)
    if mode == "absolute_mass":
        masses = [component.mass for component in rows]
        return _from_masses(mode, rows, masses, volume, temperature, pressure)
    if mode == "mass_part_total_mass":
        if total_mass is None:
            raise ValueError("total_mass is required for mass_part_total_mass")
        masses = [component.mass_part * float(total_mass) for component in rows]
        return _from_masses(mode, rows, masses, volume, temperature, pressure)
    if mode == "absolute_mole":
        moles = [component.moles for component in rows]
        return _from_moles(mode, rows, moles, volume, temperature, pressure)
    if mode == "mole_part":
        if total_moles is None:
            raise ValueError("total_moles is required for mole_part")
        moles = [component.mole_part * float(total_moles) for component in rows]
        return _from_moles(mode, rows, moles, volume, temperature, pressure)
    if mode == "concentration_and_volume":
        if volume is None:
            raise ValueError("volume is required for concentration_and_volume")
        moles = [component.concentration * float(volume) for component in rows]
        return _from_moles(mode, rows, moles, float(volume), temperature, pressure)
    if mode == "mass_part_total_mole":
        if total_moles is None:
            raise ValueError("total_moles is required for mass_part_total_mole")
        denominator = sum(component.mass_part / component.molecular_weight for component in rows)
        if denominator <= 0.0:
            raise ValueError("mass parts and molecular weights must define a positive total mole basis")
        derived_mass = float(total_moles) / denominator
        masses = [component.mass_part * derived_mass for component in rows]
        return _from_masses(mode, rows, masses, volume, temperature, pressure)
    if mode == "mole_part_total_mass":
        if total_mass is None:
            raise ValueError("total_mass is required for mole_part_total_mass")
        denominator = sum(component.mole_part * component.molecular_weight for component in rows)
        if denominator <= 0.0:
            raise ValueError("mole parts and molecular weights must define a positive total mass basis")
        derived_moles = float(total_mass) / denominator
        moles = [component.mole_part * derived_moles for component in rows]
        return _from_moles(mode, rows, moles, volume, temperature, pressure)
    raise ValueError(f"Unsupported recipe input mode: {mode}")


def make_concentration_consistent(
    components: tuple[RecipeComponent, ...] | list[RecipeComponent],
    target_substance: str,
) -> tuple[RecipeComponent, ...]:
    rows = tuple(components)
    target = _find_component(rows, target_substance)
    if target.molecular_weight <= 0.0 or target.density <= 0.0:
        raise ValueError("target molecular_weight and density must be positive")
    other_sum = sum(
        component.concentration * component.molecular_weight / component.density
        for component in rows
        if component.name != target_substance
    )
    concentration = (1.0 - other_sum) * target.density / target.molecular_weight
    if concentration < 0.0:
        raise ValueError("other components already exceed the consistency sum")
    return tuple(
        replace(component, concentration=concentration) if component.name == target_substance else component
        for component in rows
    )


def fill_remainder(
    components: tuple[RecipeComponent, ...] | list[RecipeComponent],
    target_substance: str,
    *,
    field: Literal["mass_part", "mole_part"] = "mass_part",
) -> tuple[RecipeComponent, ...]:
    rows = tuple(components)
    _find_component(rows, target_substance)
    other_sum = sum(getattr(component, field) for component in rows if component.name != target_substance)
    rest = 1.0 - other_sum
    if rest < 0.0:
        raise ValueError(f"other components already exceed the {field} sum")
    return tuple(
        replace(component, **{field: rest}) if component.name == target_substance else component
        for component in rows
    )


def consistency_sum(components: tuple[RecipeComponent, ...] | list[RecipeComponent]) -> float:
    return float(sum(component.concentration * component.molecular_weight / component.density for component in components))


def _from_masses(
    mode: RecipeInputMode,
    rows: tuple[RecipeComponent, ...],
    masses: list[float],
    volume: float | None,
    temperature: float | None,
    pressure: float | None,
) -> RecipeComposition:
    total_mass = float(sum(masses))
    moles = [mass / component.molecular_weight for mass, component in zip(masses, rows)]
    inferred_volume = _volume_from_masses(rows, masses) if volume is None else float(volume)
    return _composition(mode, rows, masses, moles, inferred_volume, total_mass, sum(moles), temperature, pressure)


def _from_moles(
    mode: RecipeInputMode,
    rows: tuple[RecipeComponent, ...],
    moles: list[float],
    volume: float | None,
    temperature: float | None,
    pressure: float | None,
) -> RecipeComposition:
    masses = [amount * component.molecular_weight for amount, component in zip(moles, rows)]
    total_mass = float(sum(masses))
    inferred_volume = _volume_from_masses(rows, masses) if volume is None else float(volume)
    return _composition(mode, rows, masses, moles, inferred_volume, total_mass, sum(moles), temperature, pressure)


def _composition(
    mode: RecipeInputMode,
    rows: tuple[RecipeComponent, ...],
    masses: list[float],
    moles: list[float],
    volume: float,
    total_mass: float,
    total_moles: float,
    temperature: float | None,
    pressure: float | None,
) -> RecipeComposition:
    if volume <= 0.0:
        raise ValueError("volume must be positive")
    components = tuple(
        replace(
            component,
            mass=float(mass),
            moles=float(amount),
            mass_part=0.0 if total_mass <= 0.0 else float(mass / total_mass),
            mole_part=0.0 if total_moles <= 0.0 else float(amount / total_moles),
            concentration=float(amount / volume),
        )
        for component, mass, amount in zip(rows, masses, moles)
    )
    return RecipeComposition(
        mode=mode,
        components=components,
        volume=float(volume),
        total_mass=float(total_mass),
        total_moles=float(total_moles),
        consistency_sum=consistency_sum(components),
        temperature=temperature,
        pressure=pressure,
    )


def _volume_from_masses(rows: tuple[RecipeComponent, ...], masses: list[float]) -> float:
    return float(sum(mass / component.density for mass, component in zip(masses, rows)))


def _require_positive_thermo(rows: tuple[RecipeComponent, ...]) -> None:
    for component in rows:
        if component.molecular_weight <= 0.0:
            raise ValueError(f"{component.name} molecular_weight must be positive")
        if component.density <= 0.0:
            raise ValueError(f"{component.name} density must be positive")


def _find_component(rows: tuple[RecipeComponent, ...], name: str) -> RecipeComponent:
    for component in rows:
        if component.name == name:
            return component
    raise ValueError(f"Unknown recipe component: {name}")


def _normalize_mode(mode: str) -> RecipeInputMode:
    allowed = {
        "absolute_mass",
        "mass_part_total_mass",
        "absolute_mole",
        "mole_part",
        "concentration_and_volume",
        "mass_part_total_mole",
        "mole_part_total_mass",
    }
    if mode not in allowed:
        raise ValueError(f"Unsupported recipe input mode: {mode}")
    return mode  # type: ignore[return-value]
