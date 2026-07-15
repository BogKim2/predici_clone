from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from predici_clone.engine import SimulationEngine
from predici_clone.validation.tutorial_projects import oregonator_kinetics_project


def main() -> None:
    for corrected in (False, True):
        project = oregonator_kinetics_project(corrected_order=corrected)
        result = SimulationEngine(project).run()
        label = "corrected_order" if corrected else "stoichiometric_order"
        print(f"{label}: success={result.success} backend={result.metadata.get('backend')}")
        for name, value in result.metadata["final_concentrations"].items():
            print(f"  {name}={value:.8g}")


if __name__ == "__main__":
    main()
