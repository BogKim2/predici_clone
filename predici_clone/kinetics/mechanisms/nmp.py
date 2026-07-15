from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NMPActivation:
    dissociation_rate: float
    capping_rate: float

    def active_fraction(self, nitroxide_concentration: float) -> float:
        reverse = self.capping_rate * max(nitroxide_concentration, 0.0)
        total = self.dissociation_rate + reverse
        return self.dissociation_rate / total if total > 0 else 0.0
