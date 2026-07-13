from __future__ import annotations

from dataclasses import dataclass
from types import SimpleNamespace
from typing import Callable

import numpy as np

from predici_clone.kinetics.reaction import FRPScheme
from predici_clone.kinetics.species import SpeciesState
from predici_clone.reactor.cstr import CSTRReactor


@dataclass(frozen=True)
class CascadeReactor:
    """Series of well-mixed CSTR stages.

    Each stage is integrated to the requested end time and its outlet state is
    used as the feed to the next stage. This is a pragmatic dynamic cascade
    approximation suitable for comparing process strategies before a full PFR
    discretization is introduced.
    """

    scheme: FRPScheme
    species: SpeciesState
    nmax: int
    residence_time: float
    feed_species: SpeciesState
    stages: int
    residence_time_schedule: Callable[[float], float] | None = None

    def __post_init__(self) -> None:
        if self.stages <= 0:
            raise ValueError("stages must be positive")
        if self.residence_time <= 0:
            raise ValueError("residence_time must be positive")

    def solve(self, t_span: tuple[float, float], *, t_eval=None):
        stage_feed = self.feed_species
        stage_species = self.species
        stage_state = None
        stage_solution = None
        stage_tau = self.residence_time / self.stages
        for _stage in range(self.stages):
            reactor = CSTRReactor(
                scheme=self.scheme,
                species=stage_species,
                nmax=self.nmax,
                residence_time=stage_tau,
                feed_species=stage_feed,
                residence_time_schedule=(
                    None if self.residence_time_schedule is None else lambda time, schedule=self.residence_time_schedule: schedule(time) / self.stages
                ),
            )
            stage_solution = reactor.solve(t_span, t_eval=t_eval)
            stage_state = stage_solution.y[:, -1]
            stage_feed = SpeciesState.from_array(stage_state[:3])
            stage_species = stage_feed
        return _CascadeSolution(stage_solution, stage_state)


class _CascadeSolution(SimpleNamespace):
    def __init__(self, solution, final_state: np.ndarray) -> None:
        super().__init__()
        self.t = solution.t
        self.y = solution.y.copy()
        self.y[:, -1] = final_state
        self.success = bool(solution.success)
        self.message = solution.message
        self.status = solution.status
