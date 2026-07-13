from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from predici_clone.engine.simulation_result import SimulationResult
from predici_clone.postprocess.moments_report import distribution_frame, report_frame


def save_simulation_result(result: SimulationResult, directory: str | Path) -> Path:
    target = Path(directory)
    target.mkdir(parents=True, exist_ok=True)

    np.savez_compressed(
        target / "distribution_history.npz",
        time=result.time,
        state_history=result.state_history,
        distribution_history=result.distribution_history,
    )
    distribution_frame(result.final_distribution, first_length=result.first_length).to_csv(
        target / "distribution_final.csv",
        index=False,
    )
    report_frame(result.final_moments).to_csv(target / "moments.csv", index=False)

    manifest = {
        "success": result.success,
        "message": result.message,
        "reactor_kind": result.reactor_kind,
        "backend": result.metadata.get("backend", "unknown"),
        "first_length": result.first_length,
        "time_points": int(result.time.size),
        "distribution_bins": int(result.final_distribution.size),
        "files": {
            "history": "distribution_history.npz",
            "final_distribution": "distribution_final.csv",
            "moments": "moments.csv",
        },
        "metadata": result.metadata,
    }
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return target / "manifest.json"


def load_result_manifest(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
