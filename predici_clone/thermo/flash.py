from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.optimize import brentq

from predici_clone.thermo.peng_robinson import PengRobinsonEOS


@dataclass(frozen=True)
class FlashResult:
    vapor_fraction: float
    liquid_composition: np.ndarray
    vapor_composition: np.ndarray
    k_values: np.ndarray
    liquid_density: float
    vapor_density: float


def pt_flash(eos: PengRobinsonEOS, temperature: float, pressure: float, composition: np.ndarray, *, iterations: int = 8) -> FlashResult:
    z = np.maximum(np.asarray(composition, dtype=float), 0.0)
    z /= z.sum()
    compounds = eos.compounds
    k_values = np.asarray(
        [
            item.critical_pressure / pressure
            * np.exp(5.373 * (1.0 + item.acentric_factor) * (1.0 - item.critical_temperature / temperature))
            for item in compounds
        ],
        dtype=float,
    )
    vapor_fraction = 0.5
    liquid = z.copy()
    vapor = z.copy()
    for _ in range(max(iterations, 1)):
        vapor_fraction = _vapor_fraction(z, k_values)
        liquid = z / (1.0 + vapor_fraction * (k_values - 1.0))
        vapor = k_values * liquid
        liquid /= liquid.sum()
        vapor /= vapor.sum()
        phi_l = eos.fugacity_coefficients(temperature, pressure, liquid, phase="liquid")
        phi_v = eos.fugacity_coefficients(temperature, pressure, vapor, phase="vapor")
        updated = np.clip(phi_l / phi_v, 1e-8, 1e8)
        if np.max(np.abs(np.log(updated / k_values))) < 1e-7:
            k_values = updated
            break
        k_values = np.sqrt(k_values * updated)
    return FlashResult(
        float(vapor_fraction),
        liquid,
        vapor,
        k_values,
        eos.density(temperature, pressure, liquid, phase="liquid"),
        eos.density(temperature, pressure, vapor, phase="vapor"),
    )


def _vapor_fraction(z: np.ndarray, k_values: np.ndarray) -> float:
    def residual(value: float) -> float:
        return float(np.sum(z * (k_values - 1.0) / (1.0 + value * (k_values - 1.0))))

    at_zero = residual(0.0)
    at_one = residual(1.0)
    if at_zero <= 0:
        return 0.0
    if at_one >= 0:
        return 1.0
    return float(brentq(residual, 0.0, 1.0, xtol=1e-12))
