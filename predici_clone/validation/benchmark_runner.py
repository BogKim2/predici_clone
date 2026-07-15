from __future__ import annotations

from dataclasses import dataclass

from predici_clone.validation.benchmarks.cascade_to_pfr import cascade_to_pfr_error
from predici_clone.validation.benchmarks.copolymer_composition_drift import copolymer_composition_drift
from predici_clone.validation.benchmarks.synthetic_frp_fit import synthetic_parameter_recovery


@dataclass(frozen=True)
class BenchmarkResult:
    name: str
    success: bool
    metric: float
    details: dict[str, float]


def run_benchmarks(level: str = "fast") -> tuple[BenchmarkResult, ...]:
    if level not in {"fast", "medium", "slow"}:
        raise ValueError("level must be fast, medium, or slow")
    cascade_error = cascade_to_pfr_error(stages=6 if level == "fast" else 12)
    fit = synthetic_parameter_recovery()
    copolymer = copolymer_composition_drift()
    return (
        BenchmarkResult("cascade_to_pfr", cascade_error < 0.35, cascade_error, {"error": cascade_error}),
        BenchmarkResult("synthetic_frp_fit", fit["local_residual"] < 1e-4, fit["local_residual"], fit),
        BenchmarkResult("copolymer_composition_drift", copolymer["absolute_error"] < 1e-12, copolymer["absolute_error"], copolymer),
    )
