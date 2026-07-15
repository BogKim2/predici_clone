from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from predici_clone.montecarlo.engine import HybridMonteCarloEngine, MCReaction


@dataclass(frozen=True)
class TauLeapResult:
    event_counts: dict[str, int]
    tau: float


def tau_leap(
    engine: HybridMonteCarloEngine,
    tau: float,
    *,
    fast_kinds: tuple[str, ...] = ("propagation",),
    max_fraction: float = 0.2,
) -> TauLeapResult:
    if tau <= 0:
        raise ValueError("tau must be positive")
    active = max(len(engine.ensemble.active_chains), 1)
    counts: dict[str, int] = {}
    for reaction in engine.reactions:
        if reaction.kind not in fast_kinds:
            continue
        expected = engine.propensity(reaction) * tau
        count = int(engine.rng.poisson(expected))
        count = min(count, max(1, int(max_fraction * active * max(1.0, tau * reaction.rate))))
        for _ in range(count):
            engine.fire(reaction)
        counts[reaction.kind] = counts.get(reaction.kind, 0) + count
        engine.event_count += count
    engine.time += tau
    return TauLeapResult(counts, float(tau))
