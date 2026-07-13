from __future__ import annotations

from predici_clone.kinetics.reaction import RateLaw, ReactionKind, ReactionStep, StepTemplate


def living_polymerization_templates() -> tuple[StepTemplate, ...]:
    return (
        StepTemplate("RAFT transfer", ReactionKind.CHAIN_TRANSFER_TO_AGENT, "GP_raft", ("GP_raft",)),
        StepTemplate("NMP reversible capping", ReactionKind.CHAIN_TRANSFER_TO_AGENT, "GP_nmp", ("GP_nmp",)),
        StepTemplate("ATRP activation", ReactionKind.INITIATION, "GP_atrp", ("GP_atrp",)),
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
