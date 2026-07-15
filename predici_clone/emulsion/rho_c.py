from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from predici_clone.emulsion.compartment import compartmentalization_factor


@dataclass(frozen=True)
class RhoCState:
    rho_distribution: np.ndarray
    c_distribution: np.ndarray

    @property
    def initiation_fraction(self) -> float:
        rho_zero = float(self.rho_distribution[0]) if self.rho_distribution.size else 0.0
        total = float(np.sum(self.rho_distribution))
        return rho_zero / total if total > 0 else 0.0

    @property
    def df_rho_c(self) -> float:
        combined = np.convolve(self.rho_distribution, self.c_distribution)
        return compartmentalization_factor(combined)

    @property
    def df_c_c(self) -> float:
        return compartmentalization_factor(self.c_distribution)
