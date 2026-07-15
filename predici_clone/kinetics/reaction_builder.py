from __future__ import annotations

from dataclasses import dataclass, replace

from predici_clone.api.component_admin import auto_declare_components
from predici_clone.api.project_schema import GeneralKineticParticipant, GeneralKineticStep, Project
from predici_clone.kinetics.reaction import RateLaw, ReactionKind, ReactionStep


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
    return (
        ReactionPattern(
            "Propagation",
            "polymer",
            ReactionKind.PROPAGATION,
            "Polymer radical growth by monomer addition",
            ("polymer_radical", "monomer"),
            ("polymer_radical",),
            ("GP_kp",),
        ),
        ReactionPattern(
            "TerminationCombination",
            "polymer",
            ReactionKind.TERMINATION_COMBINATION,
            "Two live chains combine into one dead chain",
            ("polymer_radical", "polymer_radical"),
            ("dead_polymer",),
            ("GP_ktc",),
        ),
        ReactionPattern(
            "TerminationDisproportionation",
            "polymer",
            ReactionKind.TERMINATION_DISPROPORTIONATION,
            "Two live chains terminate without chain combination",
            ("polymer_radical", "polymer_radical"),
            ("dead_polymer", "dead_polymer"),
            ("GP_ktd",),
        ),
        ReactionPattern(
            "ChainTransfer",
            "polymer",
            ReactionKind.CHAIN_TRANSFER_TO_AGENT,
            "Live chain transfers activity to a transfer agent",
            ("polymer_radical", "transfer_agent"),
            ("dead_polymer", "new_radical"),
            ("GP_cta",),
        ),
        ReactionPattern(
            "GeneralKinetic",
            "kinetic",
            None,
            "Mass-action reaction with independent stoichiometric coefficients and reaction orders",
            ("reactants",),
            ("products",),
            ("kf", "kb"),
        ),
    )


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
