from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class ReactionKind(StrEnum):
    INITIATION = "Initiation"
    PROPAGATION = "Propagation"
    TERMINATION_DISPROPORTIONATION = "TerminationDisproportionation"
    TERMINATION_COMBINATION = "TerminationCombination"
    CHAIN_TRANSFER_TO_MONOMER = "ChainTransferToMonomer"
    CHAIN_TRANSFER_TO_AGENT = "ChainTransferToAgent"
    BRANCHING = "Branching"
    SCISSION = "Scission"
    POLYMER_PARTITION = "PolymerPartition"


@dataclass(frozen=True)
class RateLaw:
    expression: str
    parameters: tuple[str, ...] = ()


@dataclass(frozen=True)
class ReactionStep:
    name: str
    kind: ReactionKind
    reactants: tuple[str, ...]
    products: tuple[str, ...]
    rate_law: RateLaw
    enabled: bool = True
    site: str = "default"
    reactor_scope: str = "all"


@dataclass(frozen=True)
class StepTemplate:
    name: str
    kind: ReactionKind
    rate_expression: str
    generic_parameters: tuple[str, ...]

    def instantiate(
        self,
        *,
        site: str,
        reactants: tuple[str, ...],
        products: tuple[str, ...],
        bindings: dict[str, float],
        reactor_scope: str = "all",
    ) -> ReactionStep:
        missing = [name for name in self.generic_parameters if name not in bindings]
        if missing:
            raise ValueError(f"Missing generic parameter bindings: {', '.join(missing)}")
        return ReactionStep(
            name=f"{self.name}:{site}",
            kind=self.kind,
            reactants=reactants,
            products=products,
            rate_law=RateLaw(self.rate_expression, tuple(bindings)),
            site=site,
            reactor_scope=reactor_scope,
        )


@dataclass(frozen=True)
class FRPScheme:
    """Minimal free-radical polymerization scheme.

    The chain distribution is stored over lengths 0..nmax. Propagation shifts
    mass from n to n+1, and termination removes live chains uniformly by kt * R.
    """

    kp: float
    kt: float
    kd: float
    initiator_efficiency: float = 0.5

    def __post_init__(self) -> None:
        for name in ("kp", "kt", "kd", "initiator_efficiency"):
            if getattr(self, name) < 0:
                raise ValueError(f"{name} must be non-negative")
