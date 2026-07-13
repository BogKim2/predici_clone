from __future__ import annotations

from predici_clone.kinetics.reaction import RateLaw, ReactionKind, ReactionStep, StepTemplate


def living_polymerization_templates() -> tuple[StepTemplate, ...]:
    return (
        StepTemplate("RAFT transfer", ReactionKind.CHAIN_TRANSFER_TO_AGENT, "GP_raft", ("GP_raft",)),
        StepTemplate("NMP reversible capping", ReactionKind.CHAIN_TRANSFER_TO_AGENT, "GP_nmp", ("GP_nmp",)),
        StepTemplate("ATRP activation", ReactionKind.INITIATION, "GP_atrp", ("GP_atrp",)),
    )


def polymer_family_templates() -> tuple[StepTemplate, ...]:
    return (
        *living_polymerization_templates(),
        StepTemplate("Polycondensation growth", ReactionKind.PROPAGATION, "GP_polycondensation", ("GP_polycondensation",)),
        StepTemplate("Polyurethane addition", ReactionKind.PROPAGATION, "GP_polyurethane", ("GP_polyurethane",)),
        StepTemplate("Polyester esterification", ReactionKind.PROPAGATION, "GP_polyester", ("GP_polyester",)),
        StepTemplate("Ziegler-Natta site propagation", ReactionKind.PROPAGATION, "GP_zn_kp", ("GP_zn_kp",)),
        StepTemplate("Catalytic site transfer", ReactionKind.CHAIN_TRANSFER_TO_AGENT, "GP_site_transfer", ("GP_site_transfer",)),
    )


def instantiate_controlled_radical_step(kind: str, *, site: str = "default", rate: float = 0.01) -> ReactionStep:
    normalized = kind.strip().upper()
    mapping = {
        "RAFT": ("raft", ReactionKind.CHAIN_TRANSFER_TO_AGENT, "GP_raft"),
        "NMP": ("nmp", ReactionKind.CHAIN_TRANSFER_TO_AGENT, "GP_nmp"),
        "ATRP": ("atrp", ReactionKind.INITIATION, "GP_atrp"),
    }
    if normalized not in mapping:
        raise ValueError(f"Unsupported controlled radical template: {kind}")
    label, reaction_kind, parameter = mapping[normalized]
    return ReactionStep(
        name=f"{label}:{site}",
        kind=reaction_kind,
        reactants=("R", "controller"),
        products=("R",),
        rate_law=RateLaw(parameter, (parameter,)),
        site=site,
    )
