from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.integrate import solve_ivp


@dataclass(frozen=True)
class ODESystem:
    variables: tuple[str, ...]
    equations: dict[str, str]
    parameters: dict[str, float]

    def solve(self, time: np.ndarray, initial: dict[str, float]) -> dict[str, np.ndarray]:
        if set(self.equations) != set(self.variables):
            raise ValueError("each ODE variable requires one equation")
        t_eval = np.asarray(time, dtype=float)
        y0 = np.asarray([initial[name] for name in self.variables], dtype=float)

        def rhs(t: float, values: np.ndarray) -> np.ndarray:
            scope = {"t": t, **self.parameters, **dict(zip(self.variables, values)), "np": np}
            return np.asarray([eval(self.equations[name], {"__builtins__": {}}, scope) for name in self.variables], dtype=float)

        result = solve_ivp(rhs, (float(t_eval[0]), float(t_eval[-1])), y0, t_eval=t_eval, rtol=1e-8, atol=1e-10)
        if not result.success:
            raise RuntimeError(result.message)
        return {name: result.y[index] for index, name in enumerate(self.variables)}
