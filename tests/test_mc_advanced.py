import numpy as np

from predici_clone.montecarlo import Chain, ChainEnsemble, HybridMonteCarloEngine, MCReaction
from predici_clone.montecarlo.backward_coupling import build_coupling_profile
from predici_clone.montecarlo.sequence import AutomaticSequenceTracker, sequence_length_distribution
from predici_clone.montecarlo.tau_leap import tau_leap
from predici_clone.montecarlo.topology import add_branch, beta_scission, radius_of_gyration, shrinking_factor


def test_tau_leaping_batches_fast_events_and_advances_time():
    ensemble = ChainEnsemble([Chain(5) for _ in range(200)], target_size=200)
    engine = HybridMonteCarloEngine(ensemble, (MCReaction("propagation", 3.0),), seed=2)

    result = tau_leap(engine, 0.2)

    assert result.event_counts["propagation"] > 0
    assert engine.time == 0.2
    assert ensemble.number_average_length > 5.0


def test_topology_sequence_and_backward_coupling_preserve_invariants():
    chain = Chain(12, sequence=list("AAAABBAAAABB"))
    linear_radius = radius_of_gyration(chain)
    add_branch(chain, 6)
    left, right = beta_scission(chain, 7)
    ensemble = ChainEnsemble([chain, left, right])
    profile = build_coupling_profile(ensemble, "branch_count", deterministic_mean=0.5)

    assert 0 < shrinking_factor(chain) < 1
    assert radius_of_gyration(chain) < linear_radius
    assert left.length + right.length == chain.length
    assert sequence_length_distribution(ensemble)["A"][4] >= 1
    assert np.isfinite(profile.value_at(6))


def test_automatic_sequence_tracker_matches_block_counting():
    tracker = AutomaticSequenceTracker()
    for monomer in "AAABB":
        tracker.append(1, monomer)
    for monomer in "AAA":
        tracker.append(2, monomer)

    assert tracker.distribution() == {"A": {3: 2}, "B": {2: 1}}
