from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from predici_clone.core.moments import MomentReport, from_discrete_distribution


@dataclass(frozen=True)
class SimulationResult:
    success: bool
    message: str
    reactor_kind: str
    time: np.ndarray
    state_history: np.ndarray
    distribution_history: np.ndarray
    first_length: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def final_distribution(self) -> np.ndarray:
        return self.distribution_history[:, -1]

    @property
    def final_moments(self) -> MomentReport:
        return from_discrete_distribution(self.final_distribution, first_length=self.first_length)

    def moment_history(self) -> dict[str, np.ndarray]:
        reports = [from_discrete_distribution(self.distribution_history[:, i], self.first_length) for i in range(self.distribution_history.shape[1])]
        return {
            "M0": np.asarray([report.m0 for report in reports]),
            "M1": np.asarray([report.m1 for report in reports]),
            "M2": np.asarray([report.m2 for report in reports]),
            "Mn": np.asarray([report.mn for report in reports]),
            "Mw": np.asarray([report.mw for report in reports]),
            "PDI": np.asarray([report.pdi for report in reports]),
        }

    def actual_values_history(self) -> list[dict[str, float]]:
        rows: list[dict[str, float]] = []
        for index, time in enumerate(self.time):
            previous = self.time[index - 1] if index else time
            rows.append(
                {
                    "step_index": float(index),
                    "time": float(time),
                    "stepsize": float(time - previous),
                    "n_variables": float(self.state_history.shape[0]),
                }
            )
        return rows
