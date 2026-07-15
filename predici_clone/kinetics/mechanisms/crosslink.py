from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class CrosslinkModel:
    functionality_a: float
    functionality_b: float

    @property
    def gel_conversion(self) -> float:
        product = (self.functionality_a - 1.0) * (self.functionality_b - 1.0)
        return float(1.0 / np.sqrt(product)) if product > 0 else np.inf

    def branching_coefficient(self, conversion: float) -> float:
        return float(max(conversion, 0.0) / self.gel_conversion) if np.isfinite(self.gel_conversion) else 0.0

    def gel_fraction(self, conversion: float) -> float:
        coefficient = self.branching_coefficient(conversion)
        if coefficient <= 1.0:
            return 0.0
        return float(np.clip(1.0 - 1.0 / coefficient, 0.0, 1.0))

    def network_state(self, conversion: float, polymer_count: float) -> dict[str, float]:
        fraction = self.gel_fraction(conversion)
        return {"PN": polymer_count * (1.0 - fraction), "RN": polymer_count * fraction, "fnet": fraction}
