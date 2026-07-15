from __future__ import annotations

from predici_clone.kinetics.copolymer_terms import TerminalModel, mayo_lewis_instantaneous_fraction, terminal_model_distribution


def copolymer_composition_drift(feed_fraction_1: float = 0.45, r1: float = 0.6, r2: float = 1.8) -> dict[str, float]:
    model = TerminalModel(r1=r1, r2=r2)
    expected = mayo_lewis_instantaneous_fraction(feed_fraction_1, model)
    distribution = terminal_model_distribution(
        feed_fraction_1=feed_fraction_1,
        r1=r1,
        r2=r2,
        propagation_probability=0.55,
        nmax=16,
        composition_bins=11,
    )
    return {
        "expected": expected,
        "observed": distribution.mean_composition(),
        "absolute_error": abs(distribution.mean_composition() - expected),
    }
