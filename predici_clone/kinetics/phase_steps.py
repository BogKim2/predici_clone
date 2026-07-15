from __future__ import annotations

from dataclasses import dataclass

from predici_clone.reactor.phases import PhaseInventory


@dataclass(frozen=True)
class PhaseExchangeResult:
    transferred: float
    residual: float


def equilibrate_partition(source: PhaseInventory, target: PhaseInventory, species: str, coefficient: float) -> PhaseExchangeResult:
    if coefficient < 0:
        raise ValueError("partition coefficient must be non-negative")
    total = source.amounts.get(species, 0.0) + target.amounts.get(species, 0.0)
    denominator = source.volume + coefficient * target.volume
    source_concentration = total / denominator if denominator > 0 else 0.0
    source_amount = source_concentration * source.volume
    target_amount = coefficient * source_concentration * target.volume
    transferred = target_amount - target.amounts.get(species, 0.0)
    source.amounts[species] = source_amount
    target.amounts[species] = target_amount
    residual = target.concentration(species) - coefficient * source.concentration(species)
    return PhaseExchangeResult(float(transferred), float(residual))


def kinetic_phase_transfer(source: PhaseInventory, target: PhaseInventory, species: str, rate: float, dt: float) -> float:
    amount = min(source.amounts.get(species, 0.0), max(rate, 0.0) * max(dt, 0.0) * source.amounts.get(species, 0.0))
    source.amounts[species] = source.amounts.get(species, 0.0) - amount
    target.amounts[species] = target.amounts.get(species, 0.0) + amount
    return float(amount)


def precipitate(phase: PhaseInventory, solid: PhaseInventory, species: str, solubility: float) -> float:
    soluble = max(solubility, 0.0) * phase.volume
    excess = max(phase.amounts.get(species, 0.0) - soluble, 0.0)
    phase.amounts[species] = phase.amounts.get(species, 0.0) - excess
    solid.amounts[species] = solid.amounts.get(species, 0.0) + excess
    return float(excess)
