from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from predici_clone.montecarlo.ensemble import Chain, ChainEnsemble
from predici_clone.montecarlo.mc_index import MCIndexRegistry


SUPPORTED_REACTIONS = {
    "initiation",
    "propagation",
    "transfer",
    "combination",
    "disproportionation",
    "transfer_to_polymer",
    "crosslink",
}


@dataclass(frozen=True)
class MCReaction:
    kind: str
    rate: float
    monomer: str = "M"
    index: str | None = None
    index_increment: float = 1.0

    def __post_init__(self) -> None:
        if self.kind not in SUPPORTED_REACTIONS:
            raise ValueError(f"Unsupported Monte-Carlo reaction: {self.kind}")
        if self.rate < 0:
            raise ValueError("reaction rate must be non-negative")


class HybridMonteCarloEngine:
    def __init__(
        self,
        ensemble: ChainEnsemble,
        reactions: tuple[MCReaction, ...],
        *,
        seed: int | None = None,
        index_registry: MCIndexRegistry | None = None,
    ) -> None:
        self.ensemble = ensemble
        self.reactions = reactions
        self.rng = np.random.default_rng(seed)
        self.index_registry = index_registry or MCIndexRegistry()
        self.time = 0.0
        self.event_count = 0

    def propensity(self, reaction: MCReaction) -> float:
        active = len(self.ensemble.active_chains)
        if reaction.kind == "initiation":
            scale = self.ensemble.control_volume
        elif reaction.kind in {"combination", "disproportionation", "transfer_to_polymer", "crosslink"}:
            scale = active * max(active - 1, 0) / (2.0 * self.ensemble.control_volume)
        else:
            scale = active
        return float(reaction.rate * scale)

    def simulate_interval(self, delta_t: float, *, max_events: int = 1_000_000) -> int:
        if delta_t < 0:
            raise ValueError("delta_t must be non-negative")
        elapsed = 0.0
        events = 0
        while elapsed < delta_t and events < max_events:
            propensities = np.asarray([self.propensity(reaction) for reaction in self.reactions], dtype=float)
            total = float(propensities.sum())
            if total <= 0:
                break
            waiting_time = -np.log(max(float(self.rng.random()), 1e-15)) / total
            if elapsed + waiting_time > delta_t:
                break
            threshold = float(self.rng.random()) * total
            selected = int(np.searchsorted(np.cumsum(propensities), threshold, side="right"))
            self.fire(self.reactions[min(selected, len(self.reactions) - 1)])
            elapsed += waiting_time
            events += 1
        self.time += float(delta_t)
        self.event_count += events
        return events

    def fire(self, reaction: MCReaction) -> None:
        active = self.ensemble.active_chains
        if reaction.kind == "initiation":
            self.ensemble.chains.append(Chain(1, sequence=[reaction.monomer]))
            return
        if not active:
            return
        first = active[int(self.rng.integers(len(active)))]
        if reaction.kind == "propagation":
            first.length += 1
            first.sequence.append(reaction.monomer)
        elif reaction.kind == "transfer":
            first.active = False
            self.ensemble.chains.append(Chain(1, sequence=[reaction.monomer]))
        elif reaction.kind == "disproportionation":
            first.active = False
            if len(active) > 1:
                second = _different_chain(active, first, self.rng)
                second.active = False
        elif reaction.kind == "combination" and len(active) > 1:
            second = _different_chain(active, first, self.rng)
            first.length += second.length
            first.sequence.extend(second.sequence)
            first.branch_points.extend(point + first.length - second.length for point in second.branch_points)
            self.index_registry.merge(first, second)
            first.active = False
            self.ensemble.chains.remove(second)
        elif reaction.kind in {"transfer_to_polymer", "crosslink"} and len(self.ensemble.chains) > 1:
            target = _different_chain(self.ensemble.chains, first, self.rng)
            target.branch_points.append(max(1, int(self.rng.integers(1, target.length + 1))))
            self.index_registry.increment(target, "branch_count")
            if reaction.kind == "crosslink":
                self.index_registry.increment(target, "crosslink_count")
        if reaction.index:
            self.index_registry.increment(first, reaction.index, reaction.index_increment)

    def getmcinfo(self, info_type: int) -> float:
        ensemble = self.ensemble
        mapping = {
            0: ensemble.moments(0),
            1: ensemble.moments(1),
            2: ensemble.moments(2),
            3: ensemble.number_average_length,
            4: ensemble.weight_average_length,
            11: _length_std(ensemble),
            12: _length_stderr(ensemble),
            13: _mean_index(ensemble, "branch_count"),
        }
        if 5 <= info_type <= 10:
            names = sorted({name for chain in ensemble.chains for name in chain.indices})
            return _mean_index(ensemble, names[info_type - 5]) if info_type - 5 < len(names) else 0.0
        if info_type not in mapping:
            raise ValueError("MC info type must be in the range 0..13")
        return float(mapping[info_type])

    def getmcaverage(self, length: float, index: str, *, interpolated: bool = True) -> float:
        grouped: dict[int, list[float]] = {}
        canonical = self.index_registry.resolve(index)
        for chain in self.ensemble.chains:
            grouped.setdefault(chain.length, []).append(chain.indices.get(canonical, 0.0))
        if not grouped:
            return 0.0
        x = np.asarray(sorted(grouped), dtype=float)
        y = np.asarray([np.mean(grouped[int(value)]) for value in x], dtype=float)
        if not interpolated:
            nearest = int(np.argmin(np.abs(x - length)))
            return float(y[nearest])
        return float(np.interp(float(length), x, y, left=y[0], right=y[-1]))


def _different_chain(chains: list[Chain], first: Chain, rng: np.random.Generator) -> Chain:
    choices = [chain for chain in chains if chain is not first]
    return choices[int(rng.integers(len(choices)))]


def _length_std(ensemble: ChainEnsemble) -> float:
    return float(np.std([chain.length for chain in ensemble.chains])) if ensemble.chains else 0.0


def _length_stderr(ensemble: ChainEnsemble) -> float:
    return _length_std(ensemble) / np.sqrt(max(len(ensemble.chains), 1))


def _mean_index(ensemble: ChainEnsemble, index: str) -> float:
    return float(np.mean([chain.indices.get(index, 0.0) for chain in ensemble.chains])) if ensemble.chains else 0.0
