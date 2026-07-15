from __future__ import annotations

import numpy as np

from predici_clone.api import IntegrationControl, Project, ReactorConfig, Recipe
from predici_clone.engine import SimulationEngine


def cascade_to_pfr_error(stages: int = 8) -> float:
    recipe = Recipe(integration=IntegrationControl(t_final=0.8, output_points=5))
    cascade = Project(reactor=ReactorConfig(kind="Cascade", nmax=24, residence_time=5.0, stages=stages), recipe=recipe)
    pfr = Project(reactor=ReactorConfig(kind="PFR", nmax=24, residence_time=5.0, axial_cells=stages), recipe=recipe)
    cascade_result = SimulationEngine(cascade).run()
    pfr_result = SimulationEngine(pfr).run()
    return float(np.linalg.norm(cascade_result.final_distribution - pfr_result.final_distribution))
