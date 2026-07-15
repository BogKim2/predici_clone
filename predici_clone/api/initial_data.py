from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from predici_clone.engine.replay import Replay


@dataclass(frozen=True)
class AssignmentTable:
    state: dict[int, int]


def initial_data_from_replay(replay: Replay, index: int = -1, assignment: AssignmentTable | None = None, state_size: int | None = None) -> tuple[np.ndarray, np.ndarray]:
    source = replay.state_history[:, index]
    if assignment is None:
        state = source.copy()
    else:
        size = state_size or (max(assignment.state.values()) + 1)
        state = np.zeros(size)
        for old, new in assignment.state.items():
            state[new] = source[old]
    return state, replay.distribution_history[:, index].copy()


def combine_initial_data(items: tuple[tuple[np.ndarray, np.ndarray], ...], weights: tuple[float, ...]) -> tuple[np.ndarray, np.ndarray]:
    if len(items) != len(weights) or not items:
        raise ValueError("initial data and weights must be non-empty and aligned")
    total = sum(weights)
    state = sum(weight * item[0] for item, weight in zip(items, weights)) / total
    distribution = sum(weight * item[1] for item, weight in zip(items, weights)) / total
    return state, distribution
