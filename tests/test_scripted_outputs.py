import pytest

from predici_clone.api import IntegrationControl, OutputConfig, Project, ReactorConfig, Recipe
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.generic_outputs import compute_generic_outputs
from predici_clone.postprocess.scripted_outputs import evaluate_expression


def test_scripted_output_uses_generic_output_variables():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=20),
        recipe=Recipe(integration=IntegrationControl(t_final=1.0, output_points=5)),
        outputs=OutputConfig(
            enabled_generic_outputs=("Mn", "custom_ratio"),
            scripted_outputs={"custom_ratio": "Mw / max(Mn, 1e-12)"},
        ),
    )
    outputs = compute_generic_outputs(SimulationEngine(project).run(), project.outputs)

    assert "custom_ratio" in outputs
    assert outputs["custom_ratio"] > 0.0


def test_scripted_output_rejects_unknown_names_and_attributes():
    with pytest.raises(ValueError):
        evaluate_expression("unknown + 1", {})
    with pytest.raises(ValueError):
        evaluate_expression("__import__('os').system('echo no')", {})


def test_scripted_output_supports_safe_loop_and_array_access():
    script = """
values = [Mn, Mw, Mz]
result = 0
for i in range(3):
    result += values[i]
"""

    value = evaluate_expression(script, {"Mn": 1.0, "Mw": 2.0, "Mz": 3.0})

    assert value == 6.0


def test_scripted_output_rejects_unsafe_script_statements():
    with pytest.raises(ValueError):
        evaluate_expression("while True:\n    result = 1", {})
    with pytest.raises(ValueError):
        evaluate_expression("result = (1).__class__", {})
