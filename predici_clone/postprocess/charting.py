from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import numpy as np

from predici_clone.postprocess.gpc import GPCProfile, distribution_to_gpc_profile


GraphicMode = Literal["distribution", "moment", "monte_carlo"]
DistributionYAxis = Literal["concentration", "weight", "gpc"]
XAxisKind = Literal["chain_length", "molmass"]
XAxisScale = Literal["linear", "logarithmic"]
MomentYAxis = Literal["mn", "mw", "concentration", "dispersity"]
MonteCarloType = Literal["relative", "absolute"]


@dataclass(frozen=True)
class ChartConfig:
    graphic_mode: GraphicMode = "distribution"
    distribution_y_axis: DistributionYAxis | None = "weight"
    x_axis_kind: XAxisKind | None = "chain_length"
    x_axis_scale: XAxisScale = "linear"
    moment_y_axis: MomentYAxis | None = None
    monte_carlo_index: int | None = None
    monte_carlo_type: MonteCarloType | None = None


@dataclass(frozen=True)
class ReferenceCurve:
    x: np.ndarray
    y: np.ndarray
    label: str = "reference"
    source: str = ""


def distribution_chart_profile(
    distribution: np.ndarray,
    config: ChartConfig,
    *,
    first_length: int = 0,
    monomer_mw: float = 100.0,
) -> GPCProfile:
    if config.graphic_mode != "distribution":
        raise ValueError("distribution_chart_profile requires graphic_mode='distribution'")
    if config.distribution_y_axis == "gpc":
        return gpc_log_weight_profile(distribution, first_length=first_length, monomer_mw=monomer_mw)
    mode = "weight" if config.distribution_y_axis == "weight" else "number"
    return distribution_to_gpc_profile(
        distribution,
        first_length=first_length,
        monomer_mw=monomer_mw,
        mode=mode,
        log_axis=config.x_axis_scale == "logarithmic",
    )


def gpc_log_weight_profile(
    distribution: np.ndarray,
    *,
    first_length: int = 0,
    monomer_mw: float = 100.0,
) -> GPCProfile:
    values = np.asarray(distribution, dtype=float)
    lengths = np.arange(first_length, first_length + values.size, dtype=float)
    molecular_weight = np.maximum(lengths * float(monomer_mw), 1e-12)
    y = np.maximum(values, 0.0) * np.maximum(lengths, 0.0) ** 2
    total = float(np.sum(y))
    if total > 0.0:
        y = y / total
    return GPCProfile(
        x=np.log10(molecular_weight),
        y=y,
        x_label="log10 molecular weight",
        y_label="W(log M)",
    )


def gpc_tail_weights(x: np.ndarray, *, strength: float = 2.0) -> np.ndarray:
    axis = np.asarray(x, dtype=float)
    if axis.size == 0:
        return np.asarray([], dtype=float)
    span = max(float(np.max(axis) - np.min(axis)), 1e-12)
    normalized = (axis - float(np.min(axis))) / span
    return 1.0 + float(strength) * normalized


def weighted_curve_residual(
    model_y: np.ndarray,
    observed_y: np.ndarray,
    *,
    weighting: Literal["uniform", "gpc_tail"] = "uniform",
    x: np.ndarray | None = None,
) -> np.ndarray:
    residual = np.asarray(model_y, dtype=float) - np.asarray(observed_y, dtype=float)
    if weighting == "uniform":
        return residual
    if weighting != "gpc_tail":
        raise ValueError(f"Unsupported weighting: {weighting}")
    if x is None:
        x = np.arange(residual.size, dtype=float)
    return residual * gpc_tail_weights(np.asarray(x, dtype=float))


def save_reference_curve(curve: ReferenceCurve, path: str | Path) -> None:
    target = Path(path)
    data = np.column_stack([curve.x, curve.y])
    np.savetxt(target, data, delimiter=",", header=f"label={curve.label};source={curve.source}", comments="# ")


def load_reference_curve(path: str | Path, *, label: str = "reference") -> ReferenceCurve:
    source = Path(path)
    data = np.loadtxt(source, delimiter=",", comments="#")
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return ReferenceCurve(x=data[:, 0], y=data[:, 1], label=label, source=str(source))


def save_structured_dump(path: str | Path, **arrays: np.ndarray) -> None:
    np.savez(Path(path), **arrays)


def load_structured_dump(path: str | Path) -> dict[str, np.ndarray]:
    with np.load(Path(path)) as data:
        return {name: np.asarray(data[name]) for name in data.files}


def import_gpc_data(path: str | Path, *, label: str = "gpc") -> ReferenceCurve:
    data = np.loadtxt(Path(path), delimiter=",", comments="#", skiprows=1)
    if data.ndim == 1:
        data = data.reshape(1, -1)
    return ReferenceCurve(x=data[:, 0], y=data[:, 1], label=label, source=str(path))
