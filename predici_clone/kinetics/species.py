from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class SpeciesState:
    """Small-molecule species for free-radical polymerization."""

    monomer: float
    initiator: float
    radicals: float = 0.0

    def as_array(self) -> np.ndarray:
        return np.asarray([self.monomer, self.initiator, self.radicals], dtype=float)

    @classmethod
    def from_array(cls, values: np.ndarray) -> "SpeciesState":
        values = np.asarray(values, dtype=float)
        return cls(monomer=float(values[0]), initiator=float(values[1]), radicals=float(values[2]))
