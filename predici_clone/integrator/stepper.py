from __future__ import annotations

import numpy as np
from scipy.integrate import solve_ivp

from predici_clone.integrator.coupled_system import CoupledSystem


def integrate(
    system: CoupledSystem,
    t_span: tuple[float, float],
    *,
    t_eval: np.ndarray | None = None,
    method: str = "BDF",
    rtol: float = 1e-7,
    atol: float = 1e-10,
):
    return solve_ivp(
        system.rhs,
        t_span,
        system.initial_state,
        t_eval=t_eval,
        method=method,
        rtol=rtol,
        atol=atol,
    )
