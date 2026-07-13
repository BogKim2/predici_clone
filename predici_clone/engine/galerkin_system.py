from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np
from scipy.integrate import solve_ivp

from predici_clone.core.galerkin import GalerkinField
from predici_clone.core.galerkin_operator import GalerkinOperatorAssembler
from predici_clone.core.grid import HPMesh
from predici_clone.kinetics.reaction import FRPScheme
from predici_clone.kinetics.species import SpeciesState


@dataclass(frozen=True)
class GalerkinPBESystem:
    mesh: HPMesh
    initial_field: GalerkinField
    propagation_rate: float
    loss_rate: float = 0.0
    source_rate: float = 0.0
    termination_combination_rate: float = 0.0
    chain_transfer_rate: float = 0.0
    scission_rate: float = 0.0

    def __post_init__(self) -> None:
        if self.initial_field.mesh != self.mesh:
            raise ValueError("initial_field mesh must match system mesh")

    def rhs(self, _t: float, coeffs: np.ndarray) -> np.ndarray:
        assembler = GalerkinOperatorAssembler(self.mesh)
        linear = assembler.rhs(
            coeffs,
            propagation_rate=self.propagation_rate,
            loss_rate=self.loss_rate,
            source_rate=self.source_rate,
        )
        nonlinear = assembler.nonlinear_rhs(
            coeffs,
            termination_combination_rate=self.termination_combination_rate,
            chain_transfer_rate=self.chain_transfer_rate,
            scission_rate=self.scission_rate,
        )
        return linear + nonlinear

    def solve(self, t_span: tuple[float, float], *, t_eval=None, method: str = "BDF"):
        return solve_ivp(self.rhs, t_span, self.initial_field.coeffs, t_eval=t_eval, method=method)


@dataclass(frozen=True)
class GalerkinFRPBatchSystem:
    mesh: HPMesh
    initial_field: GalerkinField
    species: SpeciesState
    scheme: FRPScheme

    def __post_init__(self) -> None:
        if self.initial_field.mesh != self.mesh:
            raise ValueError("initial_field mesh must match system mesh")

    def initial_state(self) -> np.ndarray:
        return np.concatenate([self.species.as_array(), self.initial_field.coeffs])

    def rhs(self, _t: float, state: np.ndarray) -> np.ndarray:
        monomer = max(float(state[0]), 0.0)
        initiator = max(float(state[1]), 0.0)
        radicals = max(float(state[2]), 0.0)
        coeffs = state[3:]
        field = GalerkinField(self.mesh, coeffs)
        chain_count = max(field.moment(0), 0.0)
        initiation = 2.0 * self.scheme.initiator_efficiency * self.scheme.kd * initiator
        propagation = self.scheme.kp * monomer * radicals
        termination = self.scheme.kt * radicals
        assembler = GalerkinOperatorAssembler(self.mesh)
        coeff_rhs = assembler.rhs(
            coeffs,
            propagation_rate=propagation,
            loss_rate=termination,
            source_rate=initiation,
        )
        species_rhs = np.asarray(
            [
                -propagation * chain_count,
                -self.scheme.kd * initiator,
                initiation - self.scheme.kt * radicals * radicals,
            ],
            dtype=float,
        )
        return np.concatenate([species_rhs, coeff_rhs])

    def solve(self, t_span: tuple[float, float], *, t_eval=None, method: str = "BDF"):
        return solve_ivp(self.rhs, t_span, self.initial_state(), t_eval=t_eval, method=method)


@dataclass(frozen=True)
class GalerkinFRPSemiBatchSystem:
    mesh: HPMesh
    initial_field: GalerkinField
    species: SpeciesState
    scheme: FRPScheme
    volume: float
    feed_rate: float
    feed_species: SpeciesState
    feed_rate_schedule: Callable[[float], float] | None = None

    def __post_init__(self) -> None:
        if self.initial_field.mesh != self.mesh:
            raise ValueError("initial_field mesh must match system mesh")
        if self.volume <= 0:
            raise ValueError("volume must be positive")
        if self.feed_rate < 0:
            raise ValueError("feed_rate must be non-negative")

    def initial_state(self) -> np.ndarray:
        return np.concatenate([self.species.as_array(), [self.volume], self.initial_field.coeffs])

    def feed_rate_at(self, time: float) -> float:
        if self.feed_rate_schedule is None:
            return float(self.feed_rate)
        return max(float(self.feed_rate_schedule(float(time))), 0.0)

    def rhs(self, t: float, state: np.ndarray) -> np.ndarray:
        monomer = max(float(state[0]), 0.0)
        initiator = max(float(state[1]), 0.0)
        radicals = max(float(state[2]), 0.0)
        volume = max(float(state[3]), 1e-14)
        coeffs = state[4:]
        field = GalerkinField(self.mesh, coeffs)
        chain_count = max(field.moment(0), 0.0)
        initiation = 2.0 * self.scheme.initiator_efficiency * self.scheme.kd * initiator
        propagation = self.scheme.kp * monomer * radicals
        termination = self.scheme.kt * radicals
        feed_rate = self.feed_rate_at(t)
        dilution = feed_rate / volume
        assembler = GalerkinOperatorAssembler(self.mesh)
        coeff_rhs = assembler.rhs(
            coeffs,
            propagation_rate=propagation,
            loss_rate=termination + dilution,
            source_rate=initiation,
        )
        reaction_species_rhs = np.asarray(
            [
                -propagation * chain_count,
                -self.scheme.kd * initiator,
                initiation - self.scheme.kt * radicals * radicals,
            ],
            dtype=float,
        )
        feed = self.feed_species.as_array()
        species_rhs = reaction_species_rhs + dilution * (feed - state[:3])
        return np.concatenate([species_rhs, [feed_rate], coeff_rhs])

    def solve(self, t_span: tuple[float, float], *, t_eval=None, method: str = "BDF"):
        return solve_ivp(self.rhs, t_span, self.initial_state(), t_eval=t_eval, method=method)


@dataclass(frozen=True)
class GalerkinFRPCSTRSystem:
    mesh: HPMesh
    initial_field: GalerkinField
    species: SpeciesState
    scheme: FRPScheme
    residence_time: float
    feed_species: SpeciesState
    residence_time_schedule: Callable[[float], float] | None = None

    def __post_init__(self) -> None:
        if self.initial_field.mesh != self.mesh:
            raise ValueError("initial_field mesh must match system mesh")
        if self.residence_time <= 0:
            raise ValueError("residence_time must be positive")

    def initial_state(self) -> np.ndarray:
        return np.concatenate([self.species.as_array(), self.initial_field.coeffs])

    def residence_time_at(self, time: float) -> float:
        if self.residence_time_schedule is None:
            return float(self.residence_time)
        return max(float(self.residence_time_schedule(float(time))), 1e-12)

    def rhs(self, t: float, state: np.ndarray) -> np.ndarray:
        monomer = max(float(state[0]), 0.0)
        initiator = max(float(state[1]), 0.0)
        radicals = max(float(state[2]), 0.0)
        coeffs = state[3:]
        field = GalerkinField(self.mesh, coeffs)
        chain_count = max(field.moment(0), 0.0)
        initiation = 2.0 * self.scheme.initiator_efficiency * self.scheme.kd * initiator
        propagation = self.scheme.kp * monomer * radicals
        termination = self.scheme.kt * radicals
        residence_time = self.residence_time_at(t)
        dilution = 1.0 / residence_time
        assembler = GalerkinOperatorAssembler(self.mesh)
        coeff_rhs = assembler.rhs(
            coeffs,
            propagation_rate=propagation,
            loss_rate=termination + dilution,
            source_rate=initiation,
        )
        reaction_species_rhs = np.asarray(
            [
                -propagation * chain_count,
                -self.scheme.kd * initiator,
                initiation - self.scheme.kt * radicals * radicals,
            ],
            dtype=float,
        )
        species_rhs = reaction_species_rhs + dilution * (self.feed_species.as_array() - state[:3])
        return np.concatenate([species_rhs, coeff_rhs])

    def solve(self, t_span: tuple[float, float], *, t_eval=None, method: str = "BDF"):
        return solve_ivp(self.rhs, t_span, self.initial_state(), t_eval=t_eval, method=method)
