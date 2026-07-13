from __future__ import annotations

import numpy as np

from matplotlib.figure import Figure


def plot_distribution(
    distribution: np.ndarray,
    *,
    first_length: int = 0,
    mode: str = "weight",
    title: str = "Molecular weight distribution",
) -> Figure:
    values = np.asarray(distribution, dtype=float)
    lengths = np.arange(first_length, first_length + values.size)
    if mode == "weight":
        y = lengths * values
        ylabel = "weight fraction"
    elif mode == "mole":
        y = values
        ylabel = "mole fraction"
    else:
        raise ValueError("mode must be 'weight' or 'mole'")
    total = float(np.sum(y))
    y = y / total if total > 0 else y

    figure = Figure(figsize=(7, 4), tight_layout=True)
    axes = figure.add_subplot(111)
    axes.plot(lengths, y, color="#26547c", linewidth=2)
    axes.set_title(title)
    axes.set_xlabel("chain length")
    axes.set_ylabel(ylabel)
    axes.grid(True, alpha=0.25)
    return figure


def save_distribution_plot(path: str, distribution: np.ndarray, *, first_length: int = 0, mode: str = "weight") -> None:
    plot_distribution(distribution, first_length=first_length, mode=mode).savefig(path, dpi=160)
