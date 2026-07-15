from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class MassStreamTable:
    time: np.ndarray
    mass_flow: np.ndarray
    temperature: np.ndarray
    interpolation: str = "linear"
    delay: float = 0.0

    def value(self, time: float) -> tuple[float, float]:
        shifted = float(time) - self.delay
        if shifted < self.time[0]:
            return 0.0, float(self.temperature[0])
        if self.interpolation == "step":
            index = int(np.searchsorted(self.time, shifted, side="right") - 1)
            return float(self.mass_flow[index]), float(self.temperature[index])
        if self.interpolation != "linear":
            raise ValueError("interpolation must be linear or step")
        return float(np.interp(shifted, self.time, self.mass_flow)), float(np.interp(shifted, self.time, self.temperature))
