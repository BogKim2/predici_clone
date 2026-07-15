from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from predici_clone.core.basis_2d import TensorDistribution2D, binomial_composition_distribution, flory_chain_distribution


@dataclass(frozen=True)
class TerminalModel:
    r1: float
    r2: float


def mayo_lewis_instantaneous_fraction(feed_fraction_1: float, model: TerminalModel) -> float:
    f1 = float(np.clip(feed_fraction_1, 0.0, 1.0))
    f2 = 1.0 - f1
    numerator = model.r1 * f1 * f1 + f1 * f2
    denominator = model.r1 * f1 * f1 + 2.0 * f1 * f2 + model.r2 * f2 * f2
    if denominator <= 0.0:
        return f1
    return float(np.clip(numerator / denominator, 0.0, 1.0))


def terminal_model_distribution(
    *,
    feed_fraction_1: float,
    r1: float,
    r2: float,
    propagation_probability: float,
    nmax: int,
    composition_bins: int,
) -> TensorDistribution2D:
    model = TerminalModel(r1=float(r1), r2=float(r2))
    polymer_fraction_1 = mayo_lewis_instantaneous_fraction(feed_fraction_1, model)
    chain = flory_chain_distribution(propagation_probability, nmax)
    composition = binomial_composition_distribution(polymer_fraction_1, composition_bins)
    return TensorDistribution2D.from_outer(chain, composition)
