from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EntryExitRates:
    entry: float
    exit: float
    disproportionation: float
    phase_transfer: float


def oligomer_entry_rate(
    aqueous_oligomers: dict[int, float],
    *,
    critical_length: int,
    entry_constant: float,
) -> float:
    return float(entry_constant * sum(value for length, value in aqueous_oligomers.items() if length >= critical_length))


def entry_exit_rates(
    aqueous_oligomers: dict[int, float],
    *,
    critical_length: int,
    entry_constant: float,
    exit_constant: float,
    radicals_per_particle: float,
    disproportionation_constant: float = 0.0,
    phase_transfer_constant: float = 0.0,
) -> EntryExitRates:
    entry = oligomer_entry_rate(aqueous_oligomers, critical_length=critical_length, entry_constant=entry_constant)
    exit_rate = exit_constant * max(radicals_per_particle, 0.0)
    return EntryExitRates(entry, exit_rate, disproportionation_constant * exit_rate, phase_transfer_constant * entry)
