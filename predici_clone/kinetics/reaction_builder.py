from __future__ import annotations

from dataclasses import dataclass, replace

from predici_clone.api.component_admin import auto_declare_components
from predici_clone.api.project_schema import GeneralKineticParticipant, GeneralKineticStep, Project
from predici_clone.kinetics.reaction import RateLaw, ReactionKind, ReactionStep
from predici_clone.kinetics.step_library import get_step_definition, step_definitions


@dataclass(frozen=True)
class ReactionPattern:
    name: str
    category: str
    kind: ReactionKind | None
    description: str
    reactant_slots: tuple[str, ...]
    product_slots: tuple[str, ...]
    parameter_slots: tuple[str, ...]


def reaction_pattern_catalog() -> tuple[ReactionPattern, ...]:
    patterns = tuple(
        ReactionPattern(
            definition.name,
            _legacy_category(definition.category),
            _legacy_kind(definition.name, definition.kind),
            definition.description,
            definition.reactant_slots,
            definition.product_slots,
            definition.parameter_slots,
        )
        for definition in step_definitions()
    )
    return patterns


def filter_reaction_patterns(text: str = "", *, category: str | None = None) -> tuple[ReactionPattern, ...]:
    needle = text.strip().lower()
    matches = []
    for pattern in reaction_pattern_catalog():
        if category and pattern.category != category:
            continue
        haystack = f"{pattern.name} {pattern.description} {pattern.category}".lower()
        if needle and needle not in haystack:
            continue
        matches.append(pattern)
    return tuple(matches)


def _legacy_category(category: str) -> str:
    if category in {"initiation", "growth", "transfer", "termination", "degradation", "special"}:
        return "polymer"
    if category == "general":
        return "kinetic"
    return category


def _legacy_kind(name: str, kind: ReactionKind | None) -> ReactionKind | None:
    if name == "TerminationDisproportionation":
        return ReactionKind.TERMINATION_DISPROPORTIONATION
    if name == "GeneralKinetic":
        return None
    return kind


def build_polymer_reaction_step(
    project: Project,
    *,
    pattern_name: str,
    reactants: tuple[str, ...],
    products: tuple[str, ...],
    parameter: str,
    site: str = "default",
    enabled: bool = True,
) -> Project:
    pattern = _pattern_by_name(pattern_name)
    if pattern.kind is None:
        raise ValueError(f"Pattern is not a polymer reaction: {pattern_name}")
    updated = auto_declare_components(
        project,
        species_names=tuple(reactants) + tuple(products),
        parameter_names=(parameter,),
    )
    step = ReactionStep(
        name=f"{pattern.name}:{site}",
        kind=pattern.kind,
        reactants=tuple(reactants),
        products=tuple(products),
        rate_law=RateLaw(parameter, (parameter,)),
        enabled=enabled,
        site=site,
    )
    return replace(updated, reaction_steps=[*updated.reaction_steps, step])


def build_general_kinetic_step(
    project: Project,
    *,
    name: str,
    reactants: tuple[GeneralKineticParticipant | tuple[str, float] | tuple[str, float, float], ...],
    products: tuple[GeneralKineticParticipant | tuple[str, float] | tuple[str, float, float], ...],
    forward_parameter: str,
    backward_parameter: str = "0",
    enabled: bool = True,
    equilibrium: bool = False,
) -> Project:
    reactant_entries = tuple(_participant(item) for item in reactants)
    product_entries = tuple(_participant(item) for item in products)
    species_names = tuple(item.species for item in (*reactant_entries, *product_entries))
    updated = auto_declare_components(
        project,
        species_names=species_names,
        parameter_names=(forward_parameter, backward_parameter),
    )
    step = GeneralKineticStep(
        name=name,
        reactants=reactant_entries,
        products=product_entries,
        forward_parameter=forward_parameter,
        backward_parameter=backward_parameter,
        enabled=enabled,
        equilibrium=equilibrium,
    )
    return replace(updated, general_kinetic_steps=[*updated.general_kinetic_steps, step])


def _pattern_by_name(name: str) -> ReactionPattern:
    try:
        name = get_step_definition(name).name
    except ValueError:
        pass
    for pattern in reaction_pattern_catalog():
        if pattern.name == name:
            return pattern
    raise ValueError(f"Unknown reaction pattern: {name}")


def _participant(
    item: GeneralKineticParticipant | tuple[str, float] | tuple[str, float, float],
) -> GeneralKineticParticipant:
    if isinstance(item, GeneralKineticParticipant):
        return item
    if len(item) == 2:
        species, stoichiometry = item
        return GeneralKineticParticipant(str(species), float(stoichiometry))
    species, stoichiometry, order = item
    return GeneralKineticParticipant(str(species), float(stoichiometry), float(order))
