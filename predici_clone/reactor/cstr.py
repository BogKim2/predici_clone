from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

from predici_clone.integrator.coupled_system import CoupledSystem
from predici_clone.integrator.stepper import integrate
from predici_clone.kinetics.rate_terms import frp_rhs
from predici_clone.kinetics.reaction import FRPScheme
from predici_clone.kinetics.species import SpeciesState


@dataclass(frozen=True)
class CSTRReactor:
    scheme: FRPScheme
    species: SpeciesState
    nmax: int
    residence_time: float
    feed_species: SpeciesState
    residence_time_schedule: Callable[[float], float] | None = None

    def __post_init__(self) -> None:
        if self.residence_time <= 0:
            raise ValueError("residence_time must be positive")

    def initial_state(self) -> np.ndarray:
        chains = np.zeros(self.nmax + 1, dtype=float)
        return np.concatenate([self.species.as_array(), chains])

    def rhs(self, t: float, y: np.ndarray) -> np.ndarray:
        feed = np.concatenate([self.feed_species.as_array(), np.zeros(self.nmax + 1)])
        return frp_rhs(t, y, self.scheme) + (feed - y) / self._residence_time(t)

    def _residence_time(self, time: float) -> float:
        if self.residence_time_schedule is None:
            return self.residence_time
        return max(float(self.residence_time_schedule(float(time))), 1e-12)

    def system(self) -> CoupledSystem:
        return CoupledSystem(self.rhs, self.initial_state())

    def solve(self, t_span: tuple[float, float], *, t_eval=None):
        return integrate(self.system(), t_span, t_eval=t_eval)
