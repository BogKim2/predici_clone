from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np


@dataclass
class Chain:
    length: int
    indices: dict[str, float] = field(default_factory=dict)
    sequence: list[str] = field(default_factory=list)
    branch_points: list[int] = field(default_factory=list)
    active: bool = True

    def __post_init__(self) -> None:
        if self.length < 1:
            raise ValueError("chain length must be positive")


@dataclass
class ChainEnsemble:
    chains: list[Chain]
    control_volume: float = 1.0
    target_size: int = 100

    def __post_init__(self) -> None:
        if self.control_volume <= 0:
            raise ValueError("control_volume must be positive")
        if self.target_size <= 0:
            raise ValueError("target_size must be positive")

    @classmethod
    def from_distribution(
        cls,
        distribution: np.ndarray,
        *,
        size: int = 100,
        first_length: int = 1,
        control_volume: float = 1.0,
        seed: int | None = None,
    ) -> ChainEnsemble:
        values = np.maximum(np.asarray(distribution, dtype=float), 0.0)
        if values.ndim != 1 or values.size == 0 or float(values.sum()) <= 0:
            raise ValueError("distribution must contain positive one-dimensional weights")
        rng = np.random.default_rng(seed)
        lengths = first_length + np.arange(values.size)
        sampled = rng.choice(lengths, size=int(size), p=values / values.sum())
        return cls([Chain(int(length)) for length in sampled], control_volume, int(size))

    @property
    def active_chains(self) -> list[Chain]:
        return [chain for chain in self.chains if chain.active]

    def moments(self, order: int, *, index: str | None = None) -> float:
        if order < 0:
            raise ValueError("moment order must be non-negative")
        if not self.chains:
            return 0.0
        weights = np.asarray(
            [chain.indices.get(index, 0.0) if index else 1.0 for chain in self.chains],
            dtype=float,
        )
        lengths = np.asarray([chain.length for chain in self.chains], dtype=float)
        return float(np.sum(weights * lengths**order) / self.control_volume)

    @property
    def number_average_length(self) -> float:
        return self.moments(1) / max(self.moments(0), 1e-30)

    @property
    def weight_average_length(self) -> float:
        return self.moments(2) / max(self.moments(1), 1e-30)

    def distribution(self) -> tuple[np.ndarray, np.ndarray]:
        if not self.chains:
            return np.empty(0, dtype=int), np.empty(0, dtype=float)
        lengths, counts = np.unique([chain.length for chain in self.chains], return_counts=True)
        return lengths.astype(int), counts.astype(float) / self.control_volume

    def resize(self, size: int, *, seed: int | None = None) -> None:
        if size <= 0:
            raise ValueError("size must be positive")
        if not self.chains:
            self.target_size = int(size)
            return
        rng = np.random.default_rng(seed)
        choices = rng.choice(len(self.chains), size=int(size), replace=True)
        self.chains = [_copy_chain(self.chains[int(index)]) for index in choices]
        self.target_size = int(size)

    def save(self, path: str | Path) -> None:
        destination = Path(path)
        np.savez_compressed(
            destination,
            lengths=np.asarray([chain.length for chain in self.chains], dtype=int),
            active=np.asarray([chain.active for chain in self.chains], dtype=bool),
            sequences=np.asarray(["\x1f".join(chain.sequence) for chain in self.chains], dtype=str),
            branch_points=np.asarray([",".join(map(str, chain.branch_points)) for chain in self.chains], dtype=str),
            control_volume=self.control_volume,
            target_size=self.target_size,
        )

    @classmethod
    def load(cls, path: str | Path) -> ChainEnsemble:
        with np.load(Path(path), allow_pickle=False) as data:
            chains = []
            for length, active, sequence, branch_points in zip(
                data["lengths"], data["active"], data["sequences"], data["branch_points"]
            ):
                chains.append(
                    Chain(
                        int(length),
                        sequence=[] if not str(sequence) else str(sequence).split("\x1f"),
                        branch_points=[] if not str(branch_points) else [int(value) for value in str(branch_points).split(",")],
                        active=bool(active),
                    )
                )
            return cls(chains, float(data["control_volume"]), int(data["target_size"]))


def _copy_chain(chain: Chain) -> Chain:
    return Chain(chain.length, dict(chain.indices), list(chain.sequence), list(chain.branch_points), chain.active)
