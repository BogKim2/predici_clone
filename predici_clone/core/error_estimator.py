from __future__ import annotations

import numpy as np

from predici_clone.core.galerkin import GalerkinField


def modal_tail_indicator(field: GalerkinField) -> np.ndarray:
    """Use the highest modal coefficient in each cell as a local smoothness indicator."""

    indicators = np.empty(field.mesh.cells, dtype=float)
    offsets = field.mesh.offsets
    for cell in range(field.mesh.cells):
        cell_coeffs = field.coeffs[offsets[cell] : offsets[cell + 1]]
        scale = max(np.linalg.norm(cell_coeffs), 1e-14)
        indicators[cell] = abs(cell_coeffs[-1]) / scale
    return indicators


def mark_largest(indicators: np.ndarray, fraction: float = 0.3) -> set[int]:
    if not 0 < fraction <= 1:
        raise ValueError("fraction must be in (0, 1]")
    count = max(1, int(np.ceil(indicators.size * fraction)))
    return set(np.argsort(indicators)[-count:].tolist())
