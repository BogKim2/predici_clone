from __future__ import annotations

from dataclasses import dataclass

from predici_clone.kinetics.reaction import ReactionKind


@dataclass(frozen=True)
class ReactionStepDefinition:
    """Declarative entry in the PREDICI-compatible reaction-step catalog."""

    name: str
    category: str
    kind: ReactionKind | None
    description: str
    reactant_slots: tuple[str, ...]
    product_slots: tuple[str, ...]
    parameter_slots: tuple[str, ...]
    rate_law: str = "mass-action"
    is_polymer: bool = False
    is_pde: bool = False
    is_phase: bool = False
    aliases: tuple[str, ...] = ()

    @property
    def keywords(self) -> tuple[str, ...]:
        return (
            self.name,
            self.category,
            self.description,
            self.rate_law,
            *self.aliases,
        )


def step_definitions() -> tuple[ReactionStepDefinition, ...]:
    definitions: list[ReactionStepDefinition] = []

    def add(
        category: str,
        kind: ReactionKind | None,
        names: tuple[str, ...],
        *,
        reactants: tuple[str, ...] = ("reactants",),
        products: tuple[str, ...] = ("products",),
        parameters: tuple[str, ...] = ("k",),
        description: str | None = None,
        rate_law: str = "mass-action",
        aliases: dict[str, tuple[str, ...]] | None = None,
        kinds: dict[str, ReactionKind | None] | None = None,
        parameter_map: dict[str, tuple[str, ...]] | None = None,
        reactant_map: dict[str, tuple[str, ...]] | None = None,
        product_map: dict[str, tuple[str, ...]] | None = None,
    ) -> None:
        polymer_categories = {"initiation", "growth", "transfer", "termination", "degradation", "special"}
        for name in names:
            definitions.append(
                ReactionStepDefinition(
                    name=name,
                    category=category,
                    kind=(kinds or {}).get(name, kind),
                    description=description or f"{name} reaction step",
                    reactant_slots=(reactant_map or {}).get(name, reactants),
                    product_slots=(product_map or {}).get(name, products),
                    parameter_slots=(parameter_map or {}).get(name, parameters),
                    rate_law=rate_law,
                    is_polymer=category in polymer_categories,
                    is_pde=category == "pde",
                    is_phase=category == "phase" or name in {"PhaseExchange", "Phasetransfer", "Precipitation"},
                    aliases=(aliases or {}).get(name, ()),
                )
            )

    add(
        "initiation",
        ReactionKind.INITIATION,
        (
            "Initiation",
            "Radical initiation",
            "Initiator decay",
            "Polyfunctional initiation",
            "Initiation in polymer phase",
            "Initiation of n-mer",
        ),
        reactants=("initiator", "monomer"),
        products=("polymer_radical",),
        parameters=("k_i",),
    )
    add(
        "growth",
        ReactionKind.PROPAGATION,
        (
            "Propagation",
            "Propagation(copolymer)",
            "Propagation(copolymer, r-value)",
            "Propagation in polymer phase",
            "Propagation of n-mer",
            "k(s)-Propagation",
        ),
        reactants=("polymer_radical", "monomer"),
        products=("polymer_radical",),
        parameters=("GP_kp",),
        rate_law="mass-action; Arrhenius; k(File); k*File",
    )
    add(
        "transfer",
        ReactionKind.CHAIN_TRANSFER_TO_AGENT,
        (
            "Transfer(monomer)",
            "Transfer(solvent)",
            "ChainTransfer",
            "Transfer(copolymer)",
            "Transfer to polymer(LCB)",
            "H-transfer with scission",
            "Cross transfer with scission",
            "Transfer with counter species",
        ),
        reactants=("polymer_radical", "transfer_species"),
        products=("dead_polymer", "new_radical"),
        parameters=("GP_cta",),
        aliases={"ChainTransfer": ("Transfer(agent)",)},
        reactant_map={"ChainTransfer": ("polymer_radical", "transfer_agent")},
        product_map={"ChainTransfer": ("dead_polymer", "new_radical")},
    )
    add(
        "termination",
        ReactionKind.TERMINATION_COMBINATION,
        (
            "TerminationCombination",
            "TerminationDisproportionation",
            "Combi/Dispro",
            "Termination(s,r)",
            "Termination(copolymer)",
            "Double termination",
            "k(s)-Termination",
            "LCB termination",
        ),
        reactants=("polymer_radical", "polymer_radical"),
        products=("dead_polymer",),
        parameters=("GP_kt",),
        aliases={
            "TerminationCombination": ("Combination",),
            "TerminationDisproportionation": ("Disproportionation",),
        },
        kinds={"TerminationDisproportionation": ReactionKind.TERMINATION_DISPROPORTIONATION},
        parameter_map={
            "TerminationCombination": ("GP_ktc",),
            "TerminationDisproportionation": ("GP_ktd",),
        },
    )
    add(
        "degradation",
        ReactionKind.DEGRADATION,
        (
            "Degradation at chain end",
            "Degradation of n-mer",
            "Degradation(s,r)",
            "Degradation(statistical)",
            "Degradation(weighted)",
            "Combi-Scission",
        ),
        reactants=("polymer",),
        products=("polymer_fragments",),
        parameters=("k_deg",),
    )
    add(
        "transport",
        ReactionKind.TRANSPORT,
        (
            "Extraction",
            "Extraction2",
            "Extraction of n-mer",
            "Extraction2 of n-mer",
            "Flow(high-mol)",
            "Flow(low-mol)",
            "Convection(high-mol)",
            "Convection(low-mol)",
            "Diffusion(high-mol)",
            "Diffusion(low-mol)",
            "Masstransfer",
            "Reactor transfer",
            "Collected flow(high-mol)",
            "Collected flow(low-mol)",
            "Collected flow(direct)",
        ),
        parameters=("transport_rate",),
    )
    add(
        "special",
        ReactionKind.BALANCE,
        (
            "Gelation",
            "PhaseExchange",
            "Phasetransfer",
            "Precipitation",
            "Change of characteristic",
            "Balance",
            "Element balance",
            "Comment",
        ),
        parameters=("coefficient",),
    )
    add(
        "general",
        ReactionKind.GENERAL,
        (
            "Elemental",
            "Elemental(efficiency)",
            "Elemental(n-th order)",
            "Elemental(user-order)",
            "Equilibrium",
            "Reversible",
            "GeneralKinetic",
            "Stoichiometry",
            "General ODE-system",
            "Bio kinetics",
        ),
        parameters=("kf", "kb"),
        description="General mass-action or power-law kinetic step",
        rate_law="mass-action; power-law; Arrhenius; user-order",
    )
    add(
        "pde",
        ReactionKind.PDE,
        (
            "PDE:Kinetic",
            "PDE:EKinetic",
            "PDE:Agglomeration",
            "PDE:AgglomerationL",
            "PDE:Breakage",
            "PDE:Convection",
            "PDE:Convection2",
            "PDE:Diffusion",
            "PDE:Diffusion2",
            "PDE:Nucleation",
            "PDE:Reaction",
            "PDE:Reaction2",
            "PDE:Reaction3",
            "PDE:ReactionBC",
            "PDE:Flux",
            "PDE:Fluidbalance",
            "PDE:Feed-Profile",
            "PDE:Recycle",
            "PDE:Transition",
            "PDE:Dirichlet",
            "PDE:Dirichlet-left",
            "PDE:Dirichlet-right",
            "PDE:Neumann",
            "PDE:Neumann2",
            "PDE:Neumann-left",
            "PDE:Neumann-right",
            "PDE:Neumann2-left",
            "PDE:Neumann2-right",
        ),
        reactants=("profile",),
        products=("profile",),
        parameters=("coefficient",),
        description="Population-balance PDE operator",
    )
    if len(definitions) != 95:
        raise AssertionError(f"Reaction-step catalog must contain 95 entries, got {len(definitions)}")
    return tuple(definitions)


def get_step_definition(name: str) -> ReactionStepDefinition:
    normalized = name.casefold()
    for definition in step_definitions():
        if definition.name.casefold() == normalized or any(alias.casefold() == normalized for alias in definition.aliases):
            return definition
    raise ValueError(f"Unknown reaction step: {name}")


def filter_step_definitions(text: str = "", *, category: str | None = None) -> tuple[ReactionStepDefinition, ...]:
    needle = text.strip().casefold()
    matches = []
    for definition in step_definitions():
        if category and definition.category != category:
            continue
        if needle and not any(needle in keyword.casefold() for keyword in definition.keywords):
            continue
        matches.append(definition)
    return tuple(matches)
