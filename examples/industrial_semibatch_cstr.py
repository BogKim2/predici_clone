from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from predici_clone.api import FRPParameters, FeedStream, InitialConditions, IntegrationControl, Project, ReactorConfig, Recipe
from predici_clone.core.moments import from_discrete_distribution
from predici_clone.engine import SimulationEngine


def run() -> None:
    kinetics = FRPParameters(kp=0.08, kt=0.05, kd=0.02, initiator_efficiency=0.6)
    recipe = Recipe(
        initial=InitialConditions(monomer=0.4, initiator=0.05),
        feed=FeedStream(monomer=3.0, initiator=0.2, rate=0.08),
        integration=IntegrationControl(t_final=25.0, output_points=80),
    )
    semibatch_project = Project(
        name="industrial semibatch example",
        reactor=ReactorConfig(kind="Semi-batch", nmax=80, volume=1.0),
        kinetics=kinetics,
        recipe=recipe,
    )
    semi = SimulationEngine(semibatch_project).run()
    semi_report = from_discrete_distribution(semi.final_distribution)

    cstr_project = Project(
        name="industrial cstr example",
        reactor=ReactorConfig(kind="CSTR", nmax=80, residence_time=8.0),
        kinetics=kinetics,
        recipe=Recipe(
            initial=InitialConditions(monomer=0.0, initiator=0.0),
            feed=FeedStream(monomer=3.0, initiator=0.2),
            integration=IntegrationControl(t_final=60.0, output_points=120),
        ),
    )
    cstr = SimulationEngine(cstr_project).run()
    cstr_report = from_discrete_distribution(cstr.final_distribution)

    print(f"semibatch Mn={semi_report.mn:.3f} Mw={semi_report.mw:.3f} PDI={semi_report.pdi:.3f}")
    print(f"cstr      Mn={cstr_report.mn:.3f} Mw={cstr_report.mw:.3f} PDI={cstr_report.pdi:.3f}")


if __name__ == "__main__":
    run()
