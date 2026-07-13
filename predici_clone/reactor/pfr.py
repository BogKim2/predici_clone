from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from predici_clone.kinetics.reaction import FRPScheme
from predici_clone.kinetics.species import SpeciesState
from predici_clone.reactor.cascade import CascadeReactor


@dataclass(frozen=True)
class PFRReactor:
    """Tube-reactor approximation using a CSTR cascade."""

    scheme: FRPScheme
    species: SpeciesState
    nmax: int
    residence_time: float
    feed_species: SpeciesState
    axial_cells: int = 12
    residence_time_schedule: Callable[[float], float] | None = None

    def solve(self, t_span: tuple[float, float], *, t_eval=None):
        return CascadeReactor(
            scheme=self.scheme,
            species=self.species,
            nmax=self.nmax,
            residence_time=self.residence_time,
            feed_species=self.feed_species,
            stages=self.axial_cells,
            residence_time_schedule=self.residence_time_schedule,
        ).solve(t_span, t_eval=t_eval)
