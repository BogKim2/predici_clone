from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from predici_clone.engine.simulation_result import SimulationResult


@dataclass
class Replay:
    time: np.ndarray
    state_history: np.ndarray
    distribution_history: np.ndarray
    first_length: int = 0
    parameters: dict[str, float] = field(default_factory=dict)
    mc_results: tuple[object, ...] | None = None

    @classmethod
    def from_result(cls, result: SimulationResult, *, parameters: dict[str, float] | None = None, mc_results: tuple[object, ...] | None = None) -> Replay:
        return cls(result.time.copy(), result.state_history.copy(), result.distribution_history.copy(), result.first_length, dict(parameters or {}), mc_results)

    def snapshot(self, index: int) -> dict[str, object]:
        return {"time": float(self.time[index]), "state": self.state_history[:, index].copy(), "distribution": self.distribution_history[:, index].copy(), "mc": None if self.mc_results is None else self.mc_results[index]}

    def evaluate_output(self, function: Callable[[float, np.ndarray, np.ndarray], float]) -> np.ndarray:
        return np.asarray([function(float(time), self.state_history[:, index], self.distribution_history[:, index]) for index, time in enumerate(self.time)])

    def save(self, path: str | Path) -> None:
        np.savez_compressed(path, time=self.time, state=self.state_history, distribution=self.distribution_history, first_length=self.first_length, parameter_names=np.asarray(list(self.parameters)), parameter_values=np.asarray(list(self.parameters.values())))

    @classmethod
    def load(cls, path: str | Path) -> Replay:
        with np.load(path, allow_pickle=False) as data:
            parameters = dict(zip(data["parameter_names"].tolist(), data["parameter_values"].astype(float).tolist()))
            return cls(data["time"], data["state"], data["distribution"], int(data["first_length"]), parameters)
