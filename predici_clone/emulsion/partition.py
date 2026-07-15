from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ThreePhasePartition:
    water: float
    polymer: float
    droplet: float

    @property
    def total(self) -> float:
        return self.water + self.polymer + self.droplet


def equilibrium_partition(
    total_amount: float,
    *,
    water_volume: float,
    polymer_volume: float,
    droplet_volume: float,
    kwp: float,
    kdp: float,
) -> ThreePhasePartition:
    if min(total_amount, water_volume, polymer_volume, droplet_volume, kwp, kdp) < 0:
        raise ValueError("amounts, volumes, and partition coefficients must be non-negative")
    denominator = water_volume + kwp * polymer_volume + kwp * kdp * droplet_volume
    water_concentration = total_amount / denominator if denominator > 0 else 0.0
    return ThreePhasePartition(
        water_concentration * water_volume,
        kwp * water_concentration * polymer_volume,
        kwp * kdp * water_concentration * droplet_volume,
    )


def relax_partition(current: ThreePhasePartition, target: ThreePhasePartition, kla: float, dt: float) -> ThreePhasePartition:
    fraction = min(max(kla * dt, 0.0), 1.0)
    return ThreePhasePartition(
        current.water + fraction * (target.water - current.water),
        current.polymer + fraction * (target.polymer - current.polymer),
        current.droplet + fraction * (target.droplet - current.droplet),
    )
