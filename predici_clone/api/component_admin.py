from __future__ import annotations

from dataclasses import replace

from predici_clone.api.project_schema import (
    Parameter,
    PolymerSpecies,
    Project,
    Substance,
    polymer_species_to_dict,
    substance_to_dict,
)


def add_substance(project: Project, substance: Substance | dict[str, object]) -> Project:
    entry = substance_to_dict(substance)
    return replace(project, substances=_upsert_named_dict(project.substances, entry))


def add_polymer_species(project: Project, polymer: PolymerSpecies | dict[str, object]) -> Project:
    entry = polymer_species_to_dict(polymer)
    return replace(project, polymers=_upsert_named_dict(project.polymers, entry))


def add_parameter(project: Project, parameter: Parameter | dict[str, object]) -> Project:
    entry = _parameter_from_entry(parameter)
    generic_parameters = dict(project.generic_parameters)
    generic_parameters[entry.name] = float(entry.value)
    parameters = [item for item in project.parameters if item.name != entry.name]
    parameters.append(entry)
    return replace(project, parameters=parameters, generic_parameters=generic_parameters)


def auto_declare_components(
    project: Project,
    *,
    species_names: tuple[str, ...] | list[str] = (),
    polymer_names: tuple[str, ...] | list[str] = (),
    parameter_names: tuple[str, ...] | list[str] = (),
) -> Project:
    updated = project
    for name in species_names:
        if name and not _has_named_dict(updated.substances, name):
            updated = add_substance(updated, Substance(name=name))
    for name in polymer_names:
        if name and not _has_named_dict(updated.polymers, name):
            updated = add_polymer_species(updated, PolymerSpecies(name=name, active=True, dead=False))
    for name in parameter_names:
        if not name or _has_parameter(updated, name):
            continue
        numeric = _numeric_constant(name)
        if numeric is None:
            updated = add_parameter(updated, Parameter(name=name, value=0.0))
        else:
            updated = add_parameter(updated, Parameter(name=name, value=numeric, kind="numeric_constant"))
    return updated


def parameter_value(project: Project, name: str, default: float = 0.0) -> float:
    if name in project.generic_parameters:
        return float(project.generic_parameters[name])
    for parameter in project.parameters:
        if parameter.name == name:
            return float(parameter.value)
    numeric = _numeric_constant(name)
    return float(default if numeric is None else numeric)


def component_references(project: Project, name: str) -> dict[str, list[str]]:
    species_refs: list[str] = []
    parameter_refs: list[str] = []
    for index, step in enumerate(project.reaction_steps):
        label = f"reaction_steps[{index}].{step.name}"
        if name in step.reactants or name in step.products:
            species_refs.append(label)
        if name == step.rate_law.expression or name in step.rate_law.parameters:
            parameter_refs.append(label)
    for index, step in enumerate(project.general_kinetic_steps):
        label = f"general_kinetic_steps[{index}].{step.name}"
        participants = [item.species for item in (*step.reactants, *step.products)]
        if name in participants:
            species_refs.append(label)
        if name in {step.forward_parameter, step.backward_parameter}:
            parameter_refs.append(label)
    return {"species": species_refs, "parameters": parameter_refs}


def _parameter_from_entry(parameter: Parameter | dict[str, object]) -> Parameter:
    if isinstance(parameter, Parameter):
        return parameter
    return Parameter(
        name=str(parameter.get("name", "")),
        value=float(parameter.get("value", 0.0)),
        unit=str(parameter.get("unit", "")),
        kind=str(parameter.get("kind", "scalar")),
        pre_exponential=_optional_float(parameter.get("pre_exponential")),
        activation_energy=_optional_float(parameter.get("activation_energy")),
    )


def _upsert_named_dict(items: list[dict[str, object]], entry: dict[str, object]) -> list[dict[str, object]]:
    name = str(entry.get("name", ""))
    return [item for item in items if str(item.get("name", "")) != name] + [entry]


def _has_named_dict(items: list[dict[str, object]], name: str) -> bool:
    return any(str(item.get("name", "")) == name for item in items)


def _has_parameter(project: Project, name: str) -> bool:
    return name in project.generic_parameters or any(parameter.name == name for parameter in project.parameters)


def _numeric_constant(name: str) -> float | None:
    try:
        return float(name)
    except ValueError:
        return None


def _optional_float(value: object) -> float | None:
    if value is None:
        return None
    return float(value)
