from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class PhaseInventory:
    name: str
    volume: float
    amounts: dict[str, float] = field(default_factory=dict)
    reactive: bool = True

    def __post_init__(self) -> None:
        if self.volume < 0 or any(value < 0 for value in self.amounts.values()):
            raise ValueError("phase volume and amounts must be non-negative")

    def concentration(self, species: str) -> float:
        return self.amounts.get(species, 0.0) / self.volume if self.volume > 0 else 0.0


@dataclass
class MultiphaseInventory:
    main: PhaseInventory
    phase1: PhaseInventory | None = None
    phase2: PhaseInventory | None = None
    own: PhaseInventory | None = None
    gas: PhaseInventory | None = None

    @property
    def phases(self) -> tuple[PhaseInventory, ...]:
        return tuple(phase for phase in (self.main, self.phase1, self.phase2, self.own, self.gas) if phase is not None)

    @property
    def total_volume(self) -> float:
        return sum(phase.volume for phase in self.phases)

    def total_amount(self, species: str) -> float:
        return sum(phase.amounts.get(species, 0.0) for phase in self.phases)

    def balances(self) -> dict[str, float]:
        species = {name for phase in self.phases for name in phase.amounts}
        return {name: self.total_amount(name) for name in sorted(species)}
