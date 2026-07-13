from __future__ import annotations

import pandas as pd

from predici_clone.api.project_schema import OutputConfig
from predici_clone.engine.simulation_result import SimulationResult
from predici_clone.postprocess.scripted_outputs import evaluate_scripted_outputs


def compute_generic_outputs(result: SimulationResult, config: OutputConfig) -> dict[str, float]:
    moments = result.final_moments
    monomer_initial = float(result.state_history[0, 0]) if result.state_history.size else 0.0
    monomer_final = float(result.state_history[0, -1]) if result.state_history.size else 0.0
    conversion = (monomer_initial - monomer_final) / monomer_initial if monomer_initial > 0 else 0.0
    available = {
        "M0": moments.m0,
        "M1": moments.m1,
        "M2": moments.m2,
        "M3": moments.m3,
        "Mn": moments.mn,
        "Mw": moments.mw,
        "Mz": moments.mz,
        "PDI": moments.pdi,
        "AMW": moments.amw,
        "mass": moments.mass,
        "conversion": conversion,
        "temperature": float(result.metadata.get("final_temperature", 0.0)),
        "heat_duty": float(result.metadata.get("final_heat_duty", 0.0)),
        "coolant_temperature": float(result.metadata.get("final_coolant_temperature", 0.0)),
        "additional_heat": float(result.metadata.get("final_additional_heat", 0.0)),
        "pressure": float(result.metadata.get("final_pressure", 1.0)),
        "feed_rate": float(result.metadata.get("scheduled_final_feed_rate", 0.0)),
        "residence_time": float(result.metadata.get("scheduled_final_residence_time", 0.0)),
    }
    scripted = evaluate_scripted_outputs(config.scripted_outputs, available) if config.scripted_outputs else {}
    available.update(scripted)
    return {name: available[name] for name in config.enabled_generic_outputs if name in available}


def generic_outputs_frame(result: SimulationResult, config: OutputConfig) -> pd.DataFrame:
    outputs = compute_generic_outputs(result, config)
    return pd.DataFrame([{"output": name, "value": value} for name, value in outputs.items()])
