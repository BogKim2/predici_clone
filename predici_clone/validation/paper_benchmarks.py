from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from predici_clone.core.moments import MomentReport, from_discrete_distribution
from predici_clone.postprocess.fitting import flory_weight_fraction, mixture_flory_weight_fraction


@dataclass(frozen=True)
class BenchmarkCase:
    name: str
    source: str
    frame: pd.DataFrame
    expected: dict[str, float]
    note: str

    def moment_report(self) -> MomentReport:
        return moments_from_frame(self.frame)


def moments_from_frame(frame: pd.DataFrame) -> MomentReport:
    lengths = frame["chain_length"].to_numpy(dtype=float)
    concentration = frame["concentration"].to_numpy(dtype=float)
    return MomentReport(
        m0=float(np.sum(concentration)),
        m1=float(np.sum(lengths * concentration)),
        m2=float(np.sum(lengths * lengths * concentration)),
        m3=float(np.sum(lengths * lengths * lengths * concentration)),
    )


def flory_step_growth_case(probability: float = 0.99, max_length: int = 5000) -> BenchmarkCase:
    """Flory-Schulz distribution for step growth / disproportionation FRP."""

    lengths = np.arange(1, max_length + 1)
    weight_fraction = flory_weight_fraction(lengths, probability)
    concentration = weight_fraction / lengths
    frame = pd.DataFrame(
        {
            "chain_length": lengths,
            "concentration": concentration,
            "weight_fraction": weight_fraction,
        }
    )
    expected_mn = 1.0 / (1.0 - probability)
    expected_mw = (1.0 + probability) / (1.0 - probability)
    return BenchmarkCase(
        name="flory_step_growth_p099",
        source="Fogler polymerization notes, equations R7.1-33 to R7.1-35",
        frame=frame,
        expected={"Mn": expected_mn, "Mw": expected_mw, "PDI": expected_mw / expected_mn},
        note="Analytic Flory-Schulz distribution at conversion p=0.99.",
    )


def fogler_fractionation_case() -> BenchmarkCase:
    """Six-fraction molecular-weight example reported in Fogler R7.1."""

    molecular_weight = np.asarray([10000, 15000, 20000, 25000, 30000, 35000], dtype=float)
    mole_fraction = np.asarray([0.10, 0.20, 0.40, 0.15, 0.10, 0.05], dtype=float)
    monomer_weight = 25.0
    lengths = (molecular_weight / monomer_weight).astype(int)
    frame = pd.DataFrame(
        {
            "chain_length": lengths,
            "molecular_weight": molecular_weight,
            "mole_fraction": mole_fraction,
            "concentration": mole_fraction,
        }
    )
    return BenchmarkCase(
        name="fogler_fractionation_example_r7_2",
        source="Fogler polymerization notes, Example R7-2",
        frame=frame,
        expected={"Mn": 820.0, "Mw": 736000.0 / 820.0, "PDI": (736000.0 / 820.0) / 820.0},
        note="Discrete fractionation table with monomer molecular weight 25 Da.",
    )


def multisite_schulz_flory_case(max_length: int = 6000) -> BenchmarkCase:
    """Broad MWD case from a weighted mixture of Schulz-Flory active sites."""

    lengths = np.arange(1, max_length + 1)
    weight_fraction = mixture_flory_weight_fraction(lengths, probabilities=[0.985, 0.995], weights=[0.35, 0.65])
    concentration = weight_fraction / lengths
    frame = pd.DataFrame(
        {
            "chain_length": lengths,
            "concentration": concentration,
            "weight_fraction": weight_fraction,
        }
    )
    report = moments_from_frame(frame)
    return BenchmarkCase(
        name="multisite_schulz_flory_broad_mwd",
        source="Ideal-reactor review: multiple catalyst sites as weighted Schulz-Flory distributions",
        frame=frame,
        expected={"Mn": report.mn, "Mw": report.mw, "PDI": report.pdi},
        note="Synthetic numerical benchmark following the cited multisite Schulz-Flory construction.",
    )


def available_cases() -> list[BenchmarkCase]:
    return [flory_step_growth_case(), fogler_fractionation_case(), multisite_schulz_flory_case()]
