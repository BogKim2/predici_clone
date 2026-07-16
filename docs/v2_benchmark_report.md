# v2.0 Benchmark Report

Date: 2026-07-15

The medium suite passes all 10 benchmarks: cascade-to-PFR, synthetic FRP recovery,
copolymer composition drift, ATRP MWD, gel point, emulsion compartment factor, MSMPR analytic
mean, Peng-Robinson fugacity, Monte Carlo chain mean, and PSD volume behavior.

The manual reproduction command `python -m test_manuals --all` passes 39/39 scenarios and writes
`test_manuals/outputs/report.html` and `result.md`.
