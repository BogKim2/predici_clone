from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np

from predici_clone.core.error_estimator import modal_tail_indicator
from predici_clone.core.galerkin import GalerkinField


AdaptStrategy = Literal["h", "p", "mixed"]


@dataclass(frozen=True)
class AdaptationResult:
    field: GalerkinField
    indicators: np.ndarray
    h_marked: set[int]
    p_marked: set[int]
    changed: bool


def adapt_galerkin_field(
    field: GalerkinField,
    *,
    tolerance: float,
    strategy: AdaptStrategy = "mixed",
    max_cells: int = 256,
    max_degree: int = 5,
) -> AdaptationResult:
    indicators = modal_tail_indicator(field)
    marked = {int(index) for index in np.flatnonzero(indicators > tolerance)}
    if not marked:
        return AdaptationResult(field, indicators, set(), set(), False)

    if strategy == "h":
        h_marked = _limit_h_marks(field, marked, max_cells)
        p_marked: set[int] = set()
    elif strategy == "p":
        h_marked = set()
        p_marked = {cell for cell in marked if field.mesh.degrees[cell] < max_degree}
    elif strategy == "mixed":
        p_marked = {cell for cell in marked if field.mesh.degrees[cell] < max_degree}
        h_marked = _limit_h_marks(field, marked - p_marked, max_cells)
    else:
        raise ValueError("strategy must be 'h', 'p', or 'mixed'")

    adapted = field
    if p_marked:
        adapted = adapted.p_refined(p_marked)
    if h_marked:
        adapted = adapted.h_refined(h_marked)
    return AdaptationResult(adapted, indicators, h_marked, p_marked, bool(h_marked or p_marked))


def _limit_h_marks(field: GalerkinField, marked: set[int], max_cells: int) -> set[int]:
    available = max(max_cells - field.mesh.cells, 0)
    if available <= 0:
        return set()
    return set(sorted(marked)[:available])
