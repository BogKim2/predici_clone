from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from predici_clone.core.galerkin import GalerkinField


@dataclass(frozen=True)
class MomentReport:
    m0: float
    m1: float
    m2: float
    m3: float = 0.0

    @property
    def mn(self) -> float:
        return self.m1 / self.m0 if self.m0 > 0 else 0.0

    @property
    def mw(self) -> float:
        return self.m2 / self.m1 if self.m1 > 0 else 0.0

    @property
    def pdi(self) -> float:
        return self.mw / self.mn if self.mn > 0 else 0.0

    @property
    def mz(self) -> float:
        return self.m3 / self.m2 if self.m2 > 0 else 0.0

    @property
    def amw(self) -> float:
        return self.mn

    @property
    def mass(self) -> float:
        return self.m1


def from_galerkin(field: GalerkinField) -> MomentReport:
    return MomentReport(field.moment(0), field.moment(1), field.moment(2), field.moment(3))


def from_discrete_distribution(distribution: np.ndarray, first_length: int = 0) -> MomentReport:
    y = np.asarray(distribution, dtype=float)
    n = np.arange(first_length, first_length + y.size, dtype=float)
    return MomentReport(
        float(np.sum(y)),
        float(np.sum(n * y)),
        float(np.sum(n * n * y)),
        float(np.sum(n * n * n * y)),
    )
