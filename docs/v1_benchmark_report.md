# v1.0 Benchmark Report

Benchmark runner: `predici_clone.validation.benchmark_runner.run_benchmarks("fast")`

Covered gates:

- `cascade_to_pfr`: cascade/PFR numerical proximity
- `synthetic_frp_fit`: local FRP parameter recovery residual
- `copolymer_composition_drift`: terminal-model 2D composition against Mayo-Lewis

The authoritative pass/fail evidence is the current `pytest -q` run, specifically
`tests/test_plan5_benchmarks.py`.
