from predici_clone.api import IntegrationControl, OutputConfig, Project, Recipe, ReactorConfig
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.generic_outputs import compute_generic_outputs, generic_outputs_frame


def test_generic_outputs_follow_project_output_config():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=20),
        recipe=Recipe(integration=IntegrationControl(t_final=1.0, output_points=5)),
        outputs=OutputConfig(enabled_generic_outputs=("Mn", "Mw", "conversion", "mass")),
    )
    result = SimulationEngine(project).run()
    outputs = compute_generic_outputs(result, project.outputs)
    frame = generic_outputs_frame(result, project.outputs)

    assert set(outputs) == {"Mn", "Mw", "conversion", "mass"}
    assert outputs["conversion"] >= 0.0
    assert list(frame.columns) == ["output", "value"]
