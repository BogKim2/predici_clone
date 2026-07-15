from __future__ import annotations

from dataclasses import dataclass

import numpy as np


R = 8.314462618


@dataclass(frozen=True)
class Compound:
    name: str
    critical_temperature: float
    critical_pressure: float
    acentric_factor: float
    molar_mass: float = 0.0


class PengRobinsonEOS:
    def __init__(self, compounds: tuple[Compound, ...], binary_interactions: np.ndarray | None = None) -> None:
        if not compounds:
            raise ValueError("at least one compound is required")
        self.compounds = compounds
        count = len(compounds)
        self.binary_interactions = np.zeros((count, count)) if binary_interactions is None else np.asarray(binary_interactions, dtype=float)
        if self.binary_interactions.shape != (count, count):
            raise ValueError("binary interaction matrix has the wrong shape")

    def pure_parameters(self, temperature: float) -> tuple[np.ndarray, np.ndarray]:
        if temperature <= 0:
            raise ValueError("temperature must be positive")
        tc = np.asarray([item.critical_temperature for item in self.compounds])
        pc = np.asarray([item.critical_pressure for item in self.compounds])
        omega = np.asarray([item.acentric_factor for item in self.compounds])
        kappa = 0.37464 + 1.54226 * omega - 0.26992 * omega**2
        alpha = (1.0 + kappa * (1.0 - np.sqrt(temperature / tc))) ** 2
        a = 0.45724 * R**2 * tc**2 / pc * alpha
        b = 0.07780 * R * tc / pc
        return a, b

    def mixture_parameters(self, temperature: float, composition: np.ndarray) -> tuple[float, float, np.ndarray]:
        x = _composition(composition, len(self.compounds))
        a, b = self.pure_parameters(temperature)
        aij = np.sqrt(np.outer(a, a)) * (1.0 - self.binary_interactions)
        return float(x @ aij @ x), float(x @ b), aij

    def compressibility_roots(self, temperature: float, pressure: float, composition: np.ndarray) -> np.ndarray:
        if pressure <= 0:
            raise ValueError("pressure must be positive")
        amix, bmix, _ = self.mixture_parameters(temperature, composition)
        a = amix * pressure / (R**2 * temperature**2)
        b = bmix * pressure / (R * temperature)
        roots = np.roots([1.0, -(1.0 - b), a - 3.0 * b**2 - 2.0 * b, -(a * b - b**2 - b**3)])
        real = np.sort(roots.real[np.abs(roots.imag) < 1e-8])
        return real[real > b]

    def fugacity_coefficients(self, temperature: float, pressure: float, composition: np.ndarray, *, phase: str = "vapor") -> np.ndarray:
        x = _composition(composition, len(self.compounds))
        ai, bi = self.pure_parameters(temperature)
        amix, bmix, aij = self.mixture_parameters(temperature, x)
        roots = self.compressibility_roots(temperature, pressure, x)
        if roots.size == 0:
            raise RuntimeError("Peng-Robinson EOS has no physical root")
        z = float(roots[0] if phase == "liquid" else roots[-1])
        a = amix * pressure / (R**2 * temperature**2)
        b = bmix * pressure / (R * temperature)
        bi_over_b = bi / bmix
        sum_a = aij @ x
        log_term = np.log((z + (1.0 + np.sqrt(2.0)) * b) / (z + (1.0 - np.sqrt(2.0)) * b))
        ln_phi = bi_over_b * (z - 1.0) - np.log(z - b)
        if abs(b) > 1e-16 and abs(amix) > 1e-30:
            ln_phi -= a / (2.0 * np.sqrt(2.0) * b) * (2.0 * sum_a / amix - bi_over_b) * log_term
        return np.exp(ln_phi)

    def density(self, temperature: float, pressure: float, composition: np.ndarray, *, phase: str = "vapor") -> float:
        x = _composition(composition, len(self.compounds))
        roots = self.compressibility_roots(temperature, pressure, x)
        z = roots[0] if phase == "liquid" else roots[-1]
        molar_mass = float(x @ np.asarray([item.molar_mass for item in self.compounds]))
        return pressure * molar_mass / (z * R * temperature)


def _composition(values: np.ndarray, count: int) -> np.ndarray:
    composition = np.maximum(np.asarray(values, dtype=float), 0.0)
    if composition.shape != (count,) or composition.sum() <= 0:
        raise ValueError("composition must match compounds and have positive sum")
    return composition / composition.sum()
