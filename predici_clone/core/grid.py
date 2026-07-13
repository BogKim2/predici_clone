from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class HPMesh:
    """One-dimensional h-p mesh for chain length."""

    edges: np.ndarray
    degrees: tuple[int, ...]

    @classmethod
    def uniform(cls, start: float, stop: float, cells: int, degree: int) -> "HPMesh":
        if cells <= 0:
            raise ValueError("cells must be positive")
        edges = np.linspace(start, stop, cells + 1, dtype=float)
        return cls(edges=edges, degrees=tuple([degree] * cells))

    def __post_init__(self) -> None:
        edges = np.asarray(self.edges, dtype=float)
        if edges.ndim != 1 or edges.size < 2:
            raise ValueError("edges must be a one-dimensional array with at least two entries")
        if np.any(np.diff(edges) <= 0):
            raise ValueError("edges must be strictly increasing")
        if len(self.degrees) != edges.size - 1:
            raise ValueError("one polynomial degree is required per cell")
        if any(degree < 0 for degree in self.degrees):
            raise ValueError("degrees must be non-negative")
        object.__setattr__(self, "edges", edges)

    @property
    def cells(self) -> int:
        return len(self.degrees)

    @property
    def widths(self) -> np.ndarray:
        return np.diff(self.edges)

    @property
    def offsets(self) -> np.ndarray:
        offsets = [0]
        for degree in self.degrees:
            offsets.append(offsets[-1] + degree + 1)
        return np.asarray(offsets, dtype=int)

    @property
    def dofs(self) -> int:
        return int(self.offsets[-1])

    def cell_bounds(self, cell: int) -> tuple[float, float]:
        return float(self.edges[cell]), float(self.edges[cell + 1])

    def refine_h(self, marked_cells: set[int]) -> "HPMesh":
        new_edges = [float(self.edges[0])]
        new_degrees: list[int] = []
        for i, degree in enumerate(self.degrees):
            left, right = self.cell_bounds(i)
            if i in marked_cells:
                mid = 0.5 * (left + right)
                new_edges.extend([mid, right])
                new_degrees.extend([degree, degree])
            else:
                new_edges.append(right)
                new_degrees.append(degree)
        return HPMesh(np.asarray(new_edges), tuple(new_degrees))

    def refine_p(self, marked_cells: set[int], amount: int = 1) -> "HPMesh":
        return HPMesh(self.edges.copy(), tuple(d + amount if i in marked_cells else d for i, d in enumerate(self.degrees)))
