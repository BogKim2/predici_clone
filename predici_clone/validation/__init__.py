"""Validation benchmark data sets and model comparisons."""

from predici_clone.validation.paper_benchmarks import (
    BenchmarkCase,
    flory_step_growth_case,
    fogler_fractionation_case,
    multisite_schulz_flory_case,
)
from predici_clone.validation.tutorial_projects import (
    oregonator_kinetics_project,
    polyethylene_basic_project,
)

__all__ = [
    "BenchmarkCase",
    "flory_step_growth_case",
    "fogler_fractionation_case",
    "multisite_schulz_flory_case",
    "oregonator_kinetics_project",
    "polyethylene_basic_project",
]
