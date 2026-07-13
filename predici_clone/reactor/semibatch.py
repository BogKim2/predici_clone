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
class SemiBatchReactor:
    scheme: FRPScheme
    species: SpeciesState
    nmax: int
    volume: float
    feed_rate: float
    feed_species: SpeciesState
    feed_rate_schedule: Callable[[float], float] | None = None

    def __post_init__(self) -> None:
        if self.volume <= 0:
            raise ValueError("volume must be positive")
        if self.feed_rate < 0:
            raise ValueError("feed_rate must be non-negative")

    def initial_state(self) -> np.ndarray:
        chains = np.zeros(self.nmax + 1, dtype=float)
        return np.concatenate([self.species.as_array(), chains, [self.volume]])

    def rhs(self, t: float, y: np.ndarray) -> np.ndarray:
        dydt = np.zeros_like(y, dtype=float)
        volume = max(y[-1], 1e-14)
        concentration_rhs = frp_rhs(t, y[:-1], self.scheme)
        feed_rate = self.feed_rate_at(t)
        dilution = feed_rate / volume
        feed = np.concatenate([self.feed_species.as_array(), np.zeros(self.nmax + 1)])
        dydt[:-1] = concentration_rhs + dilution * (feed - y[:-1])
        dydt[-1] = feed_rate
        return dydt

    def feed_rate_at(self, time: float) -> float:
        if self.feed_rate_schedule is None:
            return float(self.feed_rate)
        return max(float(self.feed_rate_schedule(float(time))), 0.0)

    def system(self) -> CoupledSystem:
        return CoupledSystem(self.rhs, self.initial_state())

    def solve(self, t_span: tuple[float, float], *, t_eval=None):
        return integrate(self.system(), t_span, t_eval=t_eval)
