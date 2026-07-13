from __future__ import annotations

import numpy as np

from predici_clone.kinetics.reaction import FRPScheme, ReactionKind, ReactionStep


def propagation_shift(distribution: np.ndarray, rate: float) -> np.ndarray:
    y = np.asarray(distribution, dtype=float)
    dy = -rate * y
    dy[1:] += rate * y[:-1]
    return dy


def termination_loss(distribution: np.ndarray, rate: float) -> np.ndarray:
    return -rate * np.asarray(distribution, dtype=float)


def termination_combination(distribution: np.ndarray, rate: float) -> np.ndarray:
    y = np.asarray(distribution, dtype=float)
    dy = -rate * y
    combined = np.convolve(y, y)[: y.size]
    dy += 0.5 * rate * combined
    return dy


def chain_transfer(distribution: np.ndarray, rate: float, target_length: int = 0) -> np.ndarray:
    y = np.asarray(distribution, dtype=float)
    dy = -rate * y
    if 0 <= target_length < y.size:
        dy[target_length] += rate * np.sum(y)
    return dy


def scission(distribution: np.ndarray, rate: float) -> np.ndarray:
    y = np.asarray(distribution, dtype=float)
    dy = np.zeros_like(y, dtype=float)
    for length, amount in enumerate(y):
        if length <= 1 or amount <= 0:
            continue
        dy[length] -= rate * amount
        left = length // 2
        right = length - left
        dy[left] += rate * amount
        if right < y.size:
            dy[right] += rate * amount
    return dy


def branching(distribution: np.ndarray, rate: float, branch_factor: float = 2.0) -> np.ndarray:
    """Approximate long-chain branching as conservative migration to longer bins.

    The current state vector has chain length only, not a separate branch-count
    dimension. This operator therefore captures the main observable effect for
    MWD workflows: material is reclassified toward an effective larger hydrodynamic
    size while preserving molecule count.
    """

    y = np.asarray(distribution, dtype=float)
    dy = -rate * y
    max_index = y.size - 1
    for length, amount in enumerate(y):
        if amount == 0.0:
            continue
        target = min(max(int(round(length * branch_factor)), 0), max_index)
        dy[target] += rate * amount
    return dy


def polymer_partition(distribution: np.ndarray, rate: float, cutoff: int | None = None) -> np.ndarray:
    """Approximate polymer partitioning as conservative exchange across a cutoff.

    PREDICI-style partition models may track multiple polymer phases. This clone
    currently stores one aggregate distribution, so the operator represents the
    net effect as redistribution between mirrored low/high chain-length bins.
    """

    y = np.asarray(distribution, dtype=float)
    pivot = int(cutoff if cutoff is not None else max((y.size - 1) // 2, 0))
    dy = -rate * y
    max_index = y.size - 1
    for length, amount in enumerate(y):
        if amount == 0.0:
            continue
        target = min(max(2 * pivot - length, 0), max_index)
        dy[target] += rate * amount
    return dy


def assemble_reaction_step_rhs(
    distribution: np.ndarray,
    step: ReactionStep,
    parameters: dict[str, float],
) -> np.ndarray:
    if not step.enabled:
        return np.zeros_like(distribution, dtype=float)
    rate = _rate_from_step(step, parameters)
    if step.kind == ReactionKind.PROPAGATION:
        return propagation_shift(distribution, rate)
    if step.kind == ReactionKind.TERMINATION_DISPROPORTIONATION:
        return termination_loss(distribution, rate)
    if step.kind == ReactionKind.TERMINATION_COMBINATION:
        return termination_combination(distribution, rate)
    if step.kind in {ReactionKind.CHAIN_TRANSFER_TO_MONOMER, ReactionKind.CHAIN_TRANSFER_TO_AGENT}:
        return chain_transfer(distribution, rate)
    if step.kind == ReactionKind.SCISSION:
        return scission(distribution, rate)
    if step.kind == ReactionKind.BRANCHING:
        return branching(distribution, rate)
    if step.kind == ReactionKind.POLYMER_PARTITION:
        return polymer_partition(distribution, rate)
    return np.zeros_like(distribution, dtype=float)


def assemble_reaction_network_rhs(
    distribution: np.ndarray,
    steps: list[ReactionStep] | tuple[ReactionStep, ...],
    parameters: dict[str, float],
) -> np.ndarray:
    total = np.zeros_like(distribution, dtype=float)
    for step in steps:
        total += assemble_reaction_step_rhs(distribution, step, parameters)
    return total


def _rate_from_step(step: ReactionStep, parameters: dict[str, float]) -> float:
    if step.rate_law.parameters:
        values = [parameters.get(name, 0.0) for name in step.rate_law.parameters]
        return float(np.prod(values))
    try:
        return float(step.rate_law.expression)
    except ValueError:
        return float(parameters.get(step.rate_law.expression, 0.0))


def frp_rhs(_t: float, y: np.ndarray, scheme: FRPScheme) -> np.ndarray:
    """Batch FRP RHS for [M, I, R, P_0..P_nmax]."""

    dydt = np.zeros_like(y, dtype=float)
    monomer = max(y[0], 0.0)
    initiator = max(y[1], 0.0)
    radicals = max(y[2], 0.0)
    chains = np.maximum(y[3:], 0.0)

    initiation = 2.0 * scheme.initiator_efficiency * scheme.kd * initiator
    propagation = scheme.kp * monomer * radicals
    termination = scheme.kt * radicals

    dydt[0] = -propagation * np.sum(chains)
    dydt[1] = -scheme.kd * initiator
    dydt[2] = initiation - scheme.kt * radicals * radicals
    dydt[3] = initiation
    dydt[3:] += propagation_shift(chains, propagation)
    dydt[3:] += termination_loss(chains, termination)
    return dydt
