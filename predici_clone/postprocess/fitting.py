from __future__ import annotations

import numpy as np
from scipy.optimize import minimize_scalar


def flory_mole_fraction(lengths: np.ndarray, probability: float) -> np.ndarray:
    if not 0 <= probability < 1:
        raise ValueError("probability must be in [0, 1)")
    lengths = np.asarray(lengths, dtype=int)
    values = (1.0 - probability) * np.power(probability, np.maximum(lengths - 1, 0))
    return values / np.sum(values)


def flory_weight_fraction(lengths: np.ndarray, probability: float) -> np.ndarray:
    mole = flory_mole_fraction(lengths, probability)
    values = np.asarray(lengths, dtype=float) * mole
    return values / np.sum(values)


def fit_flory_probability(lengths: np.ndarray, observed_weight_fraction: np.ndarray) -> float:
    lengths = np.asarray(lengths, dtype=int)
    observed = np.asarray(observed_weight_fraction, dtype=float)
    observed = observed / np.sum(observed)

    def objective(probability: float) -> float:
        predicted = flory_weight_fraction(lengths, probability)
        return float(np.mean((predicted - observed) ** 2))

    result = minimize_scalar(objective, bounds=(1e-8, 0.999999), method="bounded")
    return float(result.x)


def mixture_flory_weight_fraction(lengths: np.ndarray, probabilities: list[float], weights: list[float]) -> np.ndarray:
    if len(probabilities) != len(weights):
        raise ValueError("probabilities and weights must have the same length")
    weights_array = np.asarray(weights, dtype=float)
    weights_array = weights_array / np.sum(weights_array)
    total = np.zeros_like(np.asarray(lengths, dtype=float))
    for probability, weight in zip(probabilities, weights_array):
        total += weight * flory_weight_fraction(lengths, probability)
    return total / np.sum(total)
