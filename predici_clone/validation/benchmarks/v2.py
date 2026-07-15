from __future__ import annotations

import numpy as np

from predici_clone.emulsion.compartment import compartmentalization_factor
from predici_clone.emulsion.smith_ewart import smith_ewart_steady_state
from predici_clone.kinetics.mechanisms.atrp import ATRPParameters, atrp_batch_summary
from predici_clone.kinetics.mechanisms.crosslink import CrosslinkModel
from predici_clone.montecarlo import ChainEnsemble
from predici_clone.psd.pbe import msmpr_analytic_profile
from predici_clone.thermo.peng_robinson import Compound, PengRobinsonEOS


def v2_benchmark_metrics() -> dict[str, float]:
    atrp = atrp_batch_summary(0.8, ATRPParameters(100, 100, deactivation_rate=200))
    gel = CrosslinkModel(3, 3)
    emulsion = smith_ewart_steady_state(entry_rate=2, exit_rate=1, nmax=30)
    msmpr = msmpr_analytic_profile(np.linspace(0, 30, 3001), growth_rate=2, residence_time=1.5, nucleation_rate=1)
    ensemble = ChainEnsemble.from_distribution(np.exp(-np.arange(100) / 10), size=5000, seed=4)
    methane = Compound("methane", 190.56, 4.599e6, 0.011, 0.01604)
    eos = PengRobinsonEOS((methane,))
    phi = eos.fugacity_coefficients(300, 1e6, np.asarray([1.0]))[0]
    return {
        "atrp_pdi": float(atrp.dispersity),
        "gel_point": gel.gel_conversion,
        "emulsion_df": compartmentalization_factor(emulsion),
        "msmpr_mean_error": abs(msmpr.mean_size - 3.0),
        "mc_mean_error": abs(ensemble.number_average_length - 10.0),
        "dme_fugacity_finite": float(np.isfinite(phi)),
        "psd_volume_positive": float(msmpr.total_volume > 0),
    }
