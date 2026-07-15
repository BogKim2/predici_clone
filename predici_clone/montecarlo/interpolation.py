from __future__ import annotations

import numpy as np

from predici_clone.core.galerkin import GalerkinField
from predici_clone.core.grid import HPMesh
from predici_clone.montecarlo.ensemble import ChainEnsemble


def interpolate_chain_property(
    lengths: np.ndarray,
    values: np.ndarray,
    query: np.ndarray | float,
) -> np.ndarray:
    x = np.asarray(lengths, dtype=float)
    y = np.asarray(values, dtype=float)
    if x.ndim != 1 or y.shape != x.shape or x.size == 0:
        raise ValueError("lengths and values must be non-empty one-dimensional arrays")
    order = np.argsort(x)
    return np.interp(np.asarray(query, dtype=float), x[order], y[order], left=y[order][0], right=y[order][-1])


def ensemble_from_hp_field(
    mesh: HPMesh,
    coefficients: np.ndarray,
    *,
    size: int = 100,
    seed: int | None = None,
) -> ChainEnsemble:
    field = GalerkinField(mesh, np.asarray(coefficients, dtype=float))
    first = max(1, int(np.ceil(mesh.edges[0])))
    last = max(first, int(np.floor(mesh.edges[-1])))
    lengths = np.arange(first, last + 1, dtype=float)
    values = np.maximum(field.evaluate(lengths), 0.0)
    if values.sum() <= 0:
        raise ValueError("Galerkin field has no positive chain density")
    return ChainEnsemble.from_distribution(values, size=size, first_length=first, seed=seed)
