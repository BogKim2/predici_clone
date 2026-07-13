from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class GPCProfile:
    x: np.ndarray
    y: np.ndarray
    x_label: str
    y_label: str


def distribution_to_gpc_profile(
    distribution: np.ndarray,
    *,
    first_length: int = 0,
    monomer_mw: float = 100.0,
    mode: str = "weight",
    log_axis: bool = False,
    convolution_sigma: float | None = None,
) -> GPCProfile:
    values = np.asarray(distribution, dtype=float)
    lengths = np.arange(first_length, first_length + values.size, dtype=float)
    molecular_weight = np.maximum(lengths * float(monomer_mw), 1e-12)
    if mode == "number":
        y = values.copy()
        y_label = "number fraction"
    elif mode == "weight":
        y = values * molecular_weight
        y_label = "weight fraction"
    else:
        raise ValueError("mode must be 'number' or 'weight'")
    y = np.maximum(y, 0.0)
    if convolution_sigma is not None and convolution_sigma > 0:
        y = gaussian_convolution(y, convolution_sigma)
    total = float(np.sum(y))
    if total > 0:
        y = y / total
    x = np.log10(molecular_weight) if log_axis else molecular_weight
    return GPCProfile(
        x=x,
        y=y,
        x_label="log10 molecular weight" if log_axis else "molecular weight",
        y_label=y_label,
    )


def gaussian_convolution(values: np.ndarray, sigma: float) -> np.ndarray:
    source = np.asarray(values, dtype=float)
    radius = max(int(np.ceil(4.0 * sigma)), 1)
    grid = np.arange(-radius, radius + 1, dtype=float)
    kernel = np.exp(-0.5 * (grid / float(sigma)) ** 2)
    kernel = kernel / np.sum(kernel)
    padded = np.pad(source, radius, mode="edge")
    return np.convolve(padded, kernel, mode="same")[radius:-radius]
