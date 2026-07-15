from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RAFTEquilibrium:
    addition_rate: float
    fragmentation_rate: float

    @property
    def intermediate_fraction(self) -> float:
        total = self.addition_rate + self.fragmentation_rate
        return self.addition_rate / total if total > 0 else 0.0

    def transfer_probability(self, radical_concentration: float) -> float:
        rate = max(self.addition_rate * radical_concentration, 0.0)
        return rate / (rate + self.fragmentation_rate) if rate + self.fragmentation_rate > 0 else 0.0
