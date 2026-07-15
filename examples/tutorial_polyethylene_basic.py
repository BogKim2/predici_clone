from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from predici_clone.engine import SimulationEngine
from predici_clone.validation.tutorial_projects import polyethylene_basic_project


def main() -> None:
    project = polyethylene_basic_project()
    result = SimulationEngine(project).run()
    moments = result.final_moments
    print(f"{project.name}")
    print(f"success={result.success} backend={result.metadata.get('backend')}")
    print(f"final_monomer={result.state_history[0, -1]:.6g} final_radicals={result.state_history[2, -1]:.6g}")
    print(f"Mn={moments.mn:.6g} Mw={moments.mw:.6g} PDI={moments.pdi:.6g}")


if __name__ == "__main__":
    main()
