from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np


@dataclass(frozen=True)
class CoupledSystem:
    rhs: Callable[[float, np.ndarray], np.ndarray]
    initial_state: np.ndarray

    def __post_init__(self) -> None:
        object.__setattr__(self, "initial_state", np.asarray(self.initial_state, dtype=float))

    @property
    def size(self) -> int:
        return int(self.initial_state.size)
