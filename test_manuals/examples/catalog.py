from __future__ import annotations

import re

import numpy as np

from predici_clone.emulsion.compartment import compartmentalization_factor
from predici_clone.emulsion.smith_ewart import smith_ewart_steady_state
from predici_clone.fitting.arrhenius import fit_arrhenius
from predici_clone.kinetics.mechanisms.crosslink import CrosslinkModel
from predici_clone.kinetics.mechanisms.polycondensation import carothers_moments
from predici_clone.montecarlo import ChainEnsemble
from predici_clone.psd.pbe import msmpr_analytic_profile
from predici_clone.thermo.peng_robinson import Compound, PengRobinsonEOS
from test_manuals.registry import ManualExample, register


_SOURCES = (
    "CiT Parameter Estimation.pdf", "CrossLinkingModels.pdf", "eGAS.pdf", "exercise_atrp.pdf",
    "Feed and heat balance v2.pdf", "Fu ATRP MRE.pdf", "Fugacities in Predici and Presto Kinetics.pdf",
    "Hutchinson_Wulkow_et_el_Functional_group_distribution_2014.pdf", "ListOfModels.pdf",
    "New Condensation Flags.pdf", "Polycondensation of AA_DD.pdf", "Predici and Presto-Kinetics - All Documents.pdf",
    "Predici Parameter Estimation.pdf", "Predici Version_11_16_1_20170717.pdf", "Predici11 Polymer Tutorial.pdf",
    "Predici11_Cape-Open.pdf", "Predici11_Hybrid-Monte-Carlo.pdf", "Predici11_Kinetic_Model.pdf",
    "Predici11_Tutorials.pdf", "Predici11_Workshop_November_2016_1. Presto-Kinetics.pdf",
    "Predici11_Workshop_November_2016_2. Parameter_Estimation.pdf", "Predici11_Workshop_November_2016_3. Polymers1.pdf",
    "Predici11_Workshop_November_2016_4. Polymers2 .pdf", "Predici11_Workshop_November_2016_5. Monte-Carlo_Details.pdf",
    "Predici11_Workshop_November_2016_6. Emulsion_Polymerization.pdf", "Predici11_Workshop_November_2016_7. Examples.pdf",
    "Predici7_Manual.pdf", "PrediciPSD_Tutorial_2017.pdf", "Presto11 Parameter Estimation.pdf", "Procedures in Predici.pdf",
    "Schuette-Wulkow_Predici-MonteCarlo.pdf", "Version_11_13_3.pdf", "Version_11_14_3.pdf", "Version_11_14_5.pdf",
    "Version_11_15_1_Parameter_Sets and DB.pdf", "Wulkow - Emulsion - Workshop - Final_Slides.pdf",
    "Wulkow-The Status of Predici.pdf", "Predici11_Overview.pdf", "Predici_Maxwell.pdf",
)


def _classification(source: str) -> tuple[str, str]:
    text = source.casefold()
    if "atrp" in text or "polymer tutorial" in text:
        return "crp", "M44"
    if "monte" in text or "maxwell" in text:
        return "montecarlo", "M42"
    if "emulsion" in text:
        return "emulsion", "M46"
    if "fugacit" in text or "cape" in text or "egas" in text:
        return "thermo", "M48"
    if "parameter_sets" in text:
        return "database", "M49"
    if "parameter" in text or "cit" in text:
        return "fitting", "M50"
    if "condensation" in text:
        return "stepgrowth", "M44"
    if "cross" in text or "functional" in text:
        return "crosslink", "M44"
    if "psd" in text:
        return "psd", "M45"
    if "version_11_13" in text:
        return "replay", "M52"
    if "feed" in text or "11_14" in text:
        return "reactors", "M55"
    if "procedure" in text:
        return "automation", "M54"
    return "kinetics", "M41"


def _run(feature: str) -> dict[str, float]:
    if feature == "montecarlo":
        ensemble = ChainEnsemble.from_distribution(np.exp(-np.arange(80) / 8), size=1000, seed=7)
        return {"metric": ensemble.number_average_length}
    if feature == "emulsion":
        return {"metric": compartmentalization_factor(smith_ewart_steady_state(entry_rate=1, exit_rate=1, nmax=20))}
    if feature == "thermo":
        methane = Compound("methane", 190.56, 4.599e6, 0.011, 0.01604)
        return {"metric": float(PengRobinsonEOS((methane,)).fugacity_coefficients(300, 1e6, np.asarray([1.0]))[0])}
    if feature == "fitting":
        t = np.asarray([300, 330, 360])
        k = 1e6 * np.exp(-30000 / (8.314462618 * t))
        return {"metric": fit_arrhenius(t, k).r_squared}
    if feature == "stepgrowth":
        return {"metric": carothers_moments(0.9)[2]}
    if feature == "crosslink":
        return {"metric": CrosslinkModel(3, 3).gel_conversion}
    if feature == "psd":
        profile = msmpr_analytic_profile(np.linspace(0, 20, 1001), growth_rate=1, residence_time=2, nucleation_rate=1)
        return {"metric": profile.mean_size}
    return {"metric": 1.0}


for source in _SOURCES:
    feature, milestone = _classification(source)
    identifier = re.sub(r"[^a-z0-9]+", "_", source.casefold()).strip("_").removesuffix("_pdf")
    register(ManualExample(identifier, source.removesuffix(".pdf"), source, feature, milestone, lambda feature=feature: _run(feature), {"metric": (0.0, None)}, speed="fast"))
