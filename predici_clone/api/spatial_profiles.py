from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class FeedProfile:
    points: tuple[tuple[float, float], ...]

    def value_at(self, position: float) -> float:
        if not self.points:
            return 0.0
        x = np.asarray([point[0] for point in self.points], dtype=float)
        y = np.asarray([point[1] for point in self.points], dtype=float)
        return float(np.interp(float(position), x, y, left=y[0], right=y[-1]))


@dataclass(frozen=True)
class FlowDist:
    positions: np.ndarray
    weights: np.ndarray

    @classmethod
    def from_samples(cls, positions, weights) -> "FlowDist":
        positions_array = np.asarray(positions, dtype=float)
        weights_array = np.asarray(weights, dtype=float)
        total = float(np.sum(weights_array))
        if total > 0.0:
            weights_array = weights_array / total
        return cls(positions_array, weights_array)


@dataclass(frozen=True)
class FluidBalance:
    inventory: float
    inflow: float
    outflow: float

    @property
    def accumulation(self) -> float:
        return float(self.inflow - self.outflow)


def flow_solve(feed_profile: FeedProfile, flow_dist: FlowDist) -> float:
    if flow_dist.positions.size == 0:
        return 0.0
    values = np.asarray([feed_profile.value_at(position) for position in flow_dist.positions], dtype=float)
    return float(np.sum(values * flow_dist.weights))


def fluid_balance(inventory: float, inflow: float, outflow: float) -> FluidBalance:
    return FluidBalance(float(inventory), float(inflow), float(outflow))
