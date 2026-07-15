from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class ATRPParameters:
    monomer_to_initiator: float
    monomer_molar_mass: float
    initiator_efficiency: float = 1.0
    activation_rate: float = 1.0
    deactivation_rate: float = 100.0
    catalyst_solubility: float = np.inf

    def __post_init__(self) -> None:
        if self.monomer_to_initiator <= 0 or self.monomer_molar_mass <= 0:
            raise ValueError("monomer ratio and molar mass must be positive")
        if not 0 < self.initiator_efficiency <= 1:
            raise ValueError("initiator_efficiency must be in (0, 1]")
        if self.activation_rate < 0 or self.deactivation_rate <= 0:
            raise ValueError("activation rates must be physical")


@dataclass(frozen=True)
class ATRPSummary:
    conversion: np.ndarray
    number_average_molar_mass: np.ndarray
    dispersity: np.ndarray
    active_fraction: float
    soluble_catalyst: float
    precipitated_catalyst: float


def atrp_batch_summary(
    conversion: np.ndarray | float,
    parameters: ATRPParameters,
    *,
    catalyst_total: float = 1.0,
    initiator_molar_mass: float = 0.0,
) -> ATRPSummary:
    x = np.clip(np.asarray(conversion, dtype=float), 0.0, 1.0)
    active_fraction = parameters.activation_rate / (parameters.activation_rate + parameters.deactivation_rate)
    effective_chains = parameters.initiator_efficiency
    degree = parameters.monomer_to_initiator * x / effective_chains
    mn = float(initiator_molar_mass) + parameters.monomer_molar_mass * degree
    dispersity = 1.0 + 1.0 / np.maximum(degree, 1.0) + active_fraction
    soluble = min(float(catalyst_total), float(parameters.catalyst_solubility))
    return ATRPSummary(x, mn, dispersity, active_fraction, soluble, max(float(catalyst_total) - soluble, 0.0))
