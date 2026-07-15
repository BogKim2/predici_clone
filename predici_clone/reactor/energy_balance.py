from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING
from collections.abc import Callable

import numpy as np
from scipy.integrate import solve_ivp

if TYPE_CHECKING:
    from predici_clone.api.project_schema import HeatBalanceConfig


@dataclass(frozen=True)
class EnergyBalanceResult:
    temperature: np.ndarray
    heat_duty: np.ndarray
    method: str = "lumped_ode"


def scripted_temperature_rate(
    temperature: float,
    *,
    heat_capacity: float,
    mass: float,
    generated_heat: float,
    external_heat: float = 0.0,
    cp_derivative: float = 0.0,
    script: Callable[[dict[str, float]], float] | None = None,
) -> float:
    scope = {"temperature": temperature, "heat_capacity": heat_capacity, "mass": mass, "generated_heat": generated_heat, "external_heat": external_heat, "cp_derivative": cp_derivative}
    if script is not None:
        return float(script(scope))
    denominator = max(mass * heat_capacity, 1e-30)
    return float((generated_heat + external_heat - mass * temperature * cp_derivative) / denominator)


def compute_lumped_energy_balance(
    time: np.ndarray,
    monomer_history: np.ndarray,
    config: "HeatBalanceConfig",
    *,
    reaction_enthalpy: float = 0.0,
    coolant_temperature_history: np.ndarray | None = None,
    additional_heat_history: np.ndarray | None = None,
) -> EnergyBalanceResult:
    temperature = np.empty_like(time, dtype=float)
    heat_duty = np.zeros_like(time, dtype=float)
    temperature[0] = float(config.initial_feed_temp)
    if time.size <= 1:
        return EnergyBalanceResult(temperature=temperature, heat_duty=heat_duty)

    capacity = max(float(config.heat_capacity) * float(config.mass_holdup), 1e-12)
    ua = float(config.heat_transfer) * float(config.area) if config.use_heat_exchanger else 0.0
    coolant_default = (
        float(config.initial_feed_temp)
        if float(config.coolant_temperature) == 298.15 and float(config.initial_feed_temp) != 298.15
        else float(config.coolant_temperature)
    )
    coolant_temperature = (
        np.full_like(time, coolant_default, dtype=float)
        if coolant_temperature_history is None
        else np.asarray(coolant_temperature_history, dtype=float)
    )
    additional_heat = (
        np.full_like(time, float(config.additional_heat), dtype=float)
        if additional_heat_history is None
        else np.asarray(additional_heat_history, dtype=float)
    )
    monomer_rate = -np.gradient(np.asarray(monomer_history, dtype=float), np.asarray(time, dtype=float))
    monomer_rate = np.maximum(monomer_rate, 0.0)

    def rhs(t: float, y: np.ndarray) -> list[float]:
        generated_heat_rate = -float(reaction_enthalpy) * float(np.interp(t, time, monomer_rate))
        coolant = float(np.interp(t, time, coolant_temperature))
        external_heat = float(np.interp(t, time, additional_heat))
        exchanger_duty = ua * (float(y[0]) - coolant)
        return [(generated_heat_rate + external_heat - exchanger_duty) / capacity]

    solution = solve_ivp(
        rhs,
        (float(time[0]), float(time[-1])),
        [float(config.initial_feed_temp)],
        t_eval=np.asarray(time, dtype=float),
        method="RK45",
        rtol=1e-7,
        atol=1e-10,
    )
    if solution.success and solution.y.size:
        temperature = solution.y[0]
    heat_duty = ua * (temperature - coolant_temperature)
    return EnergyBalanceResult(temperature=temperature, heat_duty=heat_duty)
