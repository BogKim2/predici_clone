import numpy as np

from predici_clone.api import execute_public_command, run_automation_workflow


def test_automation_workflow_runs_model_recipe_simulation_and_npz_export(tmp_path):
    path = tmp_path / "automation_result.npz"

    payload = run_automation_workflow(t_final=0.2, output_points=3, nmax=6, export_path=path)

    assert payload["project"].recipe.name == "automation_recipe"
    assert payload["result"].success
    assert payload["points"].shape == (7, 2)
    assert "Mw" in payload["moments"]
    with np.load(path) as data:
        assert data["final_distribution"].shape == (7,)
        assert data["distribution_history"].shape[0] == 7


def test_public_command_dispatcher_exports_result_npz(tmp_path):
    payload = execute_public_command("RunAutomationWorkflow", t_final=0.2, output_points=3, nmax=5)
    path = execute_public_command("ExportResultNPZ", result=payload["result"], path=tmp_path / "run.npz")

    assert path.exists()
