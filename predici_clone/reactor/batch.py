from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from predici_clone.integrator.coupled_system import CoupledSystem
from predici_clone.integrator.stepper import integrate
from predici_clone.kinetics.rate_terms import frp_rhs
from predici_clone.kinetics.reaction import FRPScheme
from predici_clone.kinetics.species import SpeciesState


@dataclass(frozen=True)
class BatchReactor:
    scheme: FRPScheme
    species: SpeciesState
    nmax: int

    def initial_state(self) -> np.ndarray:
        chains = np.zeros(self.nmax + 1, dtype=float)
        return np.concatenate([self.species.as_array(), chains])

    def system(self) -> CoupledSystem:
        return CoupledSystem(lambda t, y: frp_rhs(t, y, self.scheme), self.initial_state())

    def solve(self, t_span: tuple[float, float], *, t_eval=None):
        return integrate(self.system(), t_span, t_eval=t_eval)
