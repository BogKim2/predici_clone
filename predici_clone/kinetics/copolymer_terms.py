from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from predici_clone.core.basis_2d import TensorDistribution2D, binomial_composition_distribution, flory_chain_distribution


@dataclass(frozen=True)
class TerminalModel:
    r1: float
    r2: float


@dataclass(frozen=True)
class PenultimateModel:
    propagation: np.ndarray

    def __post_init__(self) -> None:
        values = np.asarray(self.propagation, dtype=float)
        if values.ndim != 3 or values.shape[0] != values.shape[1] or values.shape[1] != values.shape[2]:
            raise ValueError("penultimate propagation coefficients must have shape (n, n, n)")
        if np.any(values < 0):
            raise ValueError("propagation coefficients must be non-negative")
        object.__setattr__(self, "propagation", values)

    @property
    def monomer_count(self) -> int:
        return int(self.propagation.shape[0])


def penultimate_probabilities(
    penultimate: int,
    terminal: int,
    feed_fractions: np.ndarray,
    model: PenultimateModel,
) -> np.ndarray:
    feed = np.maximum(np.asarray(feed_fractions, dtype=float), 0.0)
    if feed.shape != (model.monomer_count,) or feed.sum() <= 0:
        raise ValueError("feed fractions must match the model")
    rates = model.propagation[int(penultimate), int(terminal)] * feed
    return rates / rates.sum() if rates.sum() > 0 else feed / feed.sum()


def terminal_transition_matrix(feed_fractions: np.ndarray, rate_constants: np.ndarray) -> np.ndarray:
    feed = np.maximum(np.asarray(feed_fractions, dtype=float), 0.0)
    rates = np.maximum(np.asarray(rate_constants, dtype=float), 0.0)
    if rates.shape != (feed.size, feed.size) or feed.sum() <= 0:
        raise ValueError("rate matrix and feed fractions are inconsistent")
    weighted = rates * feed[np.newaxis, :]
    totals = weighted.sum(axis=1, keepdims=True)
    return np.divide(weighted, totals, out=np.zeros_like(weighted), where=totals > 0)


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
