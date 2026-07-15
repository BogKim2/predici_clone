from __future__ import annotations

from dataclasses import dataclass

from predici_clone.validation.benchmarks.cascade_to_pfr import cascade_to_pfr_error
from predici_clone.validation.benchmarks.copolymer_composition_drift import copolymer_composition_drift
from predici_clone.validation.benchmarks.synthetic_frp_fit import synthetic_parameter_recovery
from predici_clone.validation.benchmarks.v2 import v2_benchmark_metrics


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
    core = (
        BenchmarkResult("cascade_to_pfr", cascade_error < 0.35, cascade_error, {"error": cascade_error}),
        BenchmarkResult("synthetic_frp_fit", fit["local_residual"] < 1e-4, fit["local_residual"], fit),
        BenchmarkResult("copolymer_composition_drift", copolymer["absolute_error"] < 1e-12, copolymer["absolute_error"], copolymer),
    )
    if level == "fast":
        return core
    metrics = v2_benchmark_metrics()
    v2 = (
        BenchmarkResult("atrp_mwd", metrics["atrp_pdi"] < 1.1, metrics["atrp_pdi"], metrics),
        BenchmarkResult("gel_point", abs(metrics["gel_point"] - 0.5) < 1e-12, metrics["gel_point"], metrics),
        BenchmarkResult("emulsion_df", abs(metrics["emulsion_df"] - 1.0) < 1e-3, metrics["emulsion_df"], metrics),
        BenchmarkResult("msmpr_analytic", metrics["msmpr_mean_error"] < 0.05, metrics["msmpr_mean_error"], metrics),
        BenchmarkResult("dme_fugacity", metrics["dme_fugacity_finite"] == 1.0, metrics["dme_fugacity_finite"], metrics),
        BenchmarkResult("mc_composition", metrics["mc_mean_error"] < 1.0, metrics["mc_mean_error"], metrics),
        BenchmarkResult("psd_growth", metrics["psd_volume_positive"] == 1.0, metrics["psd_volume_positive"], metrics),
    )
    return (*core, *v2)
