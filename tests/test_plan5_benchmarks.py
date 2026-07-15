from predici_clone.validation.benchmark_runner import run_benchmarks


def test_plan5_fast_benchmark_runner_passes_core_contracts():
    results = run_benchmarks("fast")

    assert {result.name for result in results} == {
        "cascade_to_pfr",
        "synthetic_frp_fit",
        "copolymer_composition_drift",
    }
    assert all(result.success for result in results)
