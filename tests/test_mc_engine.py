import numpy as np

from predici_clone.montecarlo import ChainEnsemble, HybridMonteCarloEngine, MCReaction


def test_seeded_hybrid_engine_is_reproducible_and_updates_moments():
    initial = np.exp(-np.arange(40) / 8.0)
    first = ChainEnsemble.from_distribution(initial, size=500, seed=4)
    second = ChainEnsemble.from_distribution(initial, size=500, seed=4)
    reactions = (MCReaction("propagation", 0.8, monomer="A", index="A_count"),)
    engine_a = HybridMonteCarloEngine(first, reactions, seed=9)
    engine_b = HybridMonteCarloEngine(second, reactions, seed=9)

    assert engine_a.simulate_interval(0.5) > 0
    engine_b.simulate_interval(0.5)

    assert engine_a.getmcinfo(1) > 0
    assert engine_a.getmcinfo(3) == engine_b.getmcinfo(3)
    assert engine_a.getmcinfo(4) >= engine_a.getmcinfo(3)
    assert engine_a.getmcaverage(engine_a.getmcinfo(3), "A_count") >= 0


def test_ensemble_round_trip_preserves_chain_distribution(tmp_path):
    ensemble = ChainEnsemble.from_distribution(np.asarray([1.0, 2.0, 1.0]), size=40, seed=3)
    path = tmp_path / "ensemble.npz"
    ensemble.save(path)

    restored = ChainEnsemble.load(path)

    assert restored.distribution()[0].tolist() == ensemble.distribution()[0].tolist()
    assert restored.number_average_length == ensemble.number_average_length
