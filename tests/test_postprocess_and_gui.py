import os

import numpy as np

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFileDialog

from predici_clone.app.main import _smoke
from predici_clone.app.main_window import MainWindow
from predici_clone.app.workers.simulation_worker import SimulationWorker
from predici_clone.api import (
    IntegrationControl,
    Project,
    ReactorConfig,
    Recipe,
    add_feed_tank,
    add_polymer_feed,
    append_pre_schedule_step,
    set_pressure_profile,
    set_temperature_profile,
)
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.distribution_plot import plot_distribution
from predici_clone.postprocess.generic_outputs import compute_generic_outputs
from predici_clone.postprocess.moments_report import distribution_frame, write_distribution_report


def test_distribution_frame_and_csv_report(tmp_path):
    distribution = np.asarray([0.0, 0.2, 0.3, 0.5])
    frame = distribution_frame(distribution)
    assert list(frame.columns) == ["chain_length", "concentration", "mole_fraction", "weight_fraction"]

    path = tmp_path / "report.csv"
    write_distribution_report(str(path), distribution)
    assert path.exists()
    assert (tmp_path / "report.moments.csv").exists()


def test_plot_distribution_returns_figure():
    figure = plot_distribution(np.asarray([0.0, 0.2, 0.3, 0.5]))
    assert figure.axes


def test_main_window_smoke_runs_batch_and_benchmark():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.nmax.setValue(30)
    window.t_final.setValue(2.0)
    window._run_simulation()
    assert window.current_distribution.size == 31
    assert window.project_tree.topLevelItemCount() == 1
    assert window.tabs.count() >= 5

    window._load_benchmark()
    assert window.current_distribution.size > 0
    window.close()
    app.processEvents()


def test_main_window_mwd_time_slider_and_overlays_update_plot():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.nmax.setValue(24)
    window.t_final.setValue(1.0)
    window._run_simulation()

    assert window.mwd_time_slider.isEnabled()
    assert window.mwd_time_slider.maximum() == len(window.current_result.time) - 1
    window.mwd_time_slider.setValue(0)
    assert window.current_time_index == 0
    assert "time:" in window.mwd_time_label.text()

    first_distribution = window.current_distribution.copy()
    window.t_final.setValue(1.5)
    window._run_simulation()
    assert window.mwd_overlays
    assert np.asarray(window.mwd_overlays[-1]["distribution"]).shape == first_distribution.shape
    line_count_with_overlay = len(window.figure.axes[0].lines)
    assert line_count_with_overlay >= 2

    window._clear_mwd_overlays()
    assert not window.mwd_overlays
    assert len(window.figure.axes[0].lines) == 1
    window.close()
    app.processEvents()


def test_main_window_mwd_mode_axis_and_gpc_controls_redraw_plot():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.nmax.setValue(24)
    window.t_final.setValue(1.0)
    window._run_simulation()

    window.mwd_mode_selector.setCurrentText("mole fraction")
    window.mwd_axis_selector.setCurrentText("log molecular weight")
    window.mwd_gpc_toggle.setChecked(True)

    axes = window.figure.axes[0]
    assert axes.get_ylabel() == "mole fraction"
    assert axes.get_xlabel() == "log10 molecular weight"
    assert len(axes.lines[0].get_xdata()) == window.current_distribution.size
    assert np.isclose(np.sum(axes.lines[0].get_ydata()), 1.0)

    window.mwd_axis_selector.setCurrentText("chain length")
    axes = window.figure.axes[0]
    assert axes.get_xlabel() == "chain length"
    window.close()
    app.processEvents()


def test_main_entrypoint_smoke_mode_runs_and_exports_result():
    assert _smoke() == 0


def test_simulation_worker_emits_progress_log_and_finished_result():
    app = QApplication.instance() or QApplication([])
    project = Project(
        reactor=ReactorConfig(nmax=12),
        recipe=Recipe(integration=IntegrationControl(t_final=0.5, output_points=8)),
    )
    worker = SimulationWorker(project)
    progress = []
    logs = []
    finished = []

    worker.progress.connect(progress.append)
    worker.log.connect(logs.append)
    worker.finished.connect(finished.append)
    worker.run()

    assert finished and finished[0].success
    assert logs and "Running" in logs[0]
    assert progress[-1] == 1.0
    worker.deleteLater()
    app.processEvents()


def test_simulation_worker_stop_and_error_signals_are_observable():
    app = QApplication.instance() or QApplication([])
    stopped_worker = SimulationWorker(Project())
    stopped = []
    stopped_worker.finished.connect(stopped.append)
    stopped_worker.request_stop()
    stopped_worker.run()
    assert stopped and not stopped[0].success
    assert stopped[0].message == "Stopped"

    invalid_project = Project(reactor=ReactorConfig(kind="Unsupported"))
    error_worker = SimulationWorker(invalid_project)
    errors = []
    error_worker.error.connect(errors.append)
    error_worker.run()
    assert errors and "Unsupported reactor kind" in errors[0]

    stopped_worker.deleteLater()
    error_worker.deleteLater()
    app.processEvents()


def test_main_window_loads_trimmed_residual_csv(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    rows = []
    for time in (0.5, 1.0, 1.5):
        case = window._project_with_t_final(time, required_outputs=("mass", "Mn"))
        outputs = compute_generic_outputs(SimulationEngine(case).run(), case.outputs)
        rows.append(f"{time},{outputs['mass']},{outputs['Mn']}")
    csv_path = tmp_path / "residuals.csv"
    csv_path.write_text("time,mass_obs,Mn_obs\n" + "\n".join(rows), encoding="utf-8")

    window.fitting_residual_mapping_table.item(0, 3).setText("0.75")
    window.fitting_residual_mapping_table.item(0, 4).setText("1.25")
    window._add_residual_mapping_row()
    window.fitting_residual_mapping_table.item(1, 0).setText("Mn")
    window.fitting_residual_mapping_table.item(1, 1).setText("Mn_obs")
    window.fitting_residual_mapping_table.item(1, 3).setText("0.75")
    window.fitting_residual_mapping_table.item(1, 4).setText("1.25")
    window._load_residual_csv(csv_path)

    assert window.fitting_residual_dataset is not None
    assert window.fitting_residual_dataset.frame["time"].tolist() == [1.0]
    assert window.fitting_residual_table.rowCount() == 2
    assert window.fitting_residual_table.item(0, 2).text() == "mass"
    assert window.fitting_residual_table.item(1, 2).text() == "Mn"
    assert abs(float(window.fitting_residual_table.item(0, 6).text())) < 1e-8
    assert abs(float(window.fitting_residual_table.item(1, 6).text())) < 1e-8
    assert window.fitting_residual_figure.axes
    window.fitting_residual_mapping_table.selectRow(1)
    window._remove_selected_residual_mapping_row()
    assert window.fitting_residual_mapping_table.rowCount() == 1
    window.close()
    app.processEvents()


def test_main_window_fitting_parameter_table_supports_multiple_rows():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window._add_fitting_parameter_row()
    window.fitting_parameter_table.item(1, 0).setText("GP_kt")
    window.fitting_parameter_table.item(1, 1).setText("0.05")
    window.fitting_parameter_table.item(1, 2).setText("0.001")
    window.fitting_parameter_table.item(1, 3).setText("1.0")
    window.fitting_parameter_table.item(1, 4).setText("True")

    specs = window._parameter_specs_from_table()

    assert [spec.name for spec in specs] == ["GP_kp", "GP_kt"]
    assert specs[1].fixed
    window.fitting_parameter_table.selectRow(1)
    window._remove_selected_fitting_parameter_row()
    assert window.fitting_parameter_table.rowCount() == 1
    window.close()
    app.processEvents()


def test_main_window_multi_experiment_bayesian_updates_result_table():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.fitting_experiment_table.item(0, 1).setText("0.5")
    window.fitting_experiment_table.item(1, 1).setText("0.8")

    window._multi_experiment_bayesian_sample()

    values = {
        window.fitting_result_table.item(row, 0).text(): window.fitting_result_table.item(row, 1).text()
        for row in range(window.fitting_result_table.rowCount())
    }
    assert values["samples"] == "32"
    assert values["experiments"] == "2"
    assert "GP_kp_mean" in values
    window.close()
    app.processEvents()


def test_main_window_project_save_and_open_roundtrip(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.reactor_kind.setCurrentText("CSTR")
    window.nmax.setValue(45)
    window.t_final.setValue(4.5)
    window.kp.setValue(0.123)
    window.stages.setValue(9)
    window.axial_cells.setValue(15)
    window.backend.setCurrentText("galerkin_direct")
    window.galerkin_cells.setValue(11)
    window.galerkin_degree.setValue(3)

    path = tmp_path / "gui_project.predici.json"
    window._save_project_to_path(path)

    window.reactor_kind.setCurrentText("Batch")
    window.nmax.setValue(90)
    window.kp.setValue(0.5)
    window._open_project_from_path(path)

    assert window.current_project_path == path
    assert window.reactor_kind.currentText() == "CSTR"
    assert window.nmax.value() == 45
    assert window.kp.value() == 0.123
    assert window.stages.value() == 9
    assert window.axial_cells.value() == 15
    assert window.backend.currentText() == "galerkin_direct"
    assert window.galerkin_cells.value() == 11
    assert window.galerkin_degree.value() == 3
    assert window.project_tree.topLevelItem(0).text(0) == "PREDICI Clone Project"
    window.close()
    app.processEvents()


def test_main_window_model_builder_adds_reaction_step():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window._add_default_reaction_step()

    assert len(window.project.reaction_steps) == 1
    assert window.reaction_table.rowCount() == 1
    assert window.project.generic_parameters["GP_kp"] == window.project.kinetics.kp
    window.reaction_kind_selector.setCurrentText("ChainTransferToMonomer")
    window._add_selected_reaction_step()
    assert window.project.reaction_steps[-1].kind.value == "ChainTransferToMonomer"
    assert "GP_ctr" in window.project.generic_parameters
    window.close()
    app.processEvents()


def test_main_window_run_control_populates_actual_values_table():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.t_final.setValue(2.0)
    window.run_to_time_input.setValue(0.5)

    window._run_to_time_from_controls()

    assert window.current_result is not None
    assert window.current_result.time[-1] == 0.5
    assert window.actual_values_table.rowCount() == len(window.current_result.time)
    assert window.actual_values_table.item(window.actual_values_table.rowCount() - 1, 1).text() == "0.5"

    window._single_step_from_controls()

    assert window.current_result.time[-1] > 0.5
    assert window.actual_values_table.rowCount() == len(window.current_result.time)
    window.close()
    app.processEvents()


def test_main_window_model_builder_applies_reaction_table_edits():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window._add_default_reaction_step()

    window.reaction_table.item(0, 0).setText("no")
    window.reaction_table.item(0, 1).setText("transfer_site_b")
    window.reaction_table.item(0, 2).setText("ChainTransferToAgent")
    window.reaction_table.item(0, 3).setText("site_b")
    window.reaction_table.item(0, 4).setText("R;CTA")
    window.reaction_table.item(0, 5).setText("P0;R")
    window.reaction_table.item(0, 6).setText("GP_cta")

    window._apply_reaction_table_edits()

    step = window.project.reaction_steps[0]
    assert not step.enabled
    assert step.name == "transfer_site_b"
    assert step.kind.value == "ChainTransferToAgent"
    assert step.site == "site_b"
    assert step.reactants == ("R", "CTA")
    assert step.products == ("P0", "R")
    assert step.rate_law.parameters == ("GP_cta",)
    assert "GP_cta" in window.project.generic_parameters
    window._undo_project_edit()
    assert window.project.reaction_steps[0].kind.value == "Propagation"
    window.close()
    app.processEvents()


def test_main_window_undo_redo_project_edits():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window._add_default_reaction_step()
    assert len(window.project.reaction_steps) == 1
    assert window.undo_action.isEnabled()

    window._undo_project_edit()
    assert len(window.project.reaction_steps) == 0
    assert window.redo_action.isEnabled()

    window._redo_project_edit()
    assert len(window.project.reaction_steps) == 1
    window.reaction_table.selectRow(0)
    window._remove_selected_reaction_step()
    assert len(window.project.reaction_steps) == 0

    window._undo_project_edit()
    assert len(window.project.reaction_steps) == 1
    window.close()
    app.processEvents()


def test_main_window_inspector_shows_validation_messages():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.project = Project(reactor=ReactorConfig(nmax=0))

    window._populate_project_inspector()

    values = {
        window.inspector.item(row, 0).text(): window.inspector.item(row, 1).text()
        for row in range(window.inspector.rowCount())
    }
    assert values["validation errors"] == "1"
    assert any("reactor.nmax" in value for value in values.values())
    window.close()
    app.processEvents()


def test_main_window_recipe_table_tracks_controls():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.feed_rate.setValue(0.33)
    window.t_final.setValue(7.5)
    window.stages.setValue(8)
    window.backend.setCurrentText("galerkin")
    window.project = set_temperature_profile(window.project, [(0.0, 300.0), (1.0, 310.0)])
    window.project = set_pressure_profile(window.project, [(0.0, 1.0)])
    window.project = append_pre_schedule_step(window.project, 0.5, "set_feed_rate", rate=0.2)

    window._refresh_recipe_table_from_controls()

    values = {
        (window.recipe_table.item(row, 0).text(), window.recipe_table.item(row, 1).text()): window.recipe_table.item(row, 2).text()
        for row in range(window.recipe_table.rowCount())
    }
    assert values[("feed", "rate")] == "0.33"
    assert values[("integration", "t_final")] == "7.5"
    assert values[("integration", "backend")] == "galerkin"
    assert values[("reactor", "stages")] == "8"
    assert values[("profile", "temperature_points")] == "2"
    assert values[("profile", "pressure_points")] == "1"
    assert values[("profile", "pre_schedule_steps")] == "1"
    window.close()
    app.processEvents()


def test_main_window_recipe_table_applies_edits_to_project_and_controls():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window._populate_recipe_table()
    row_by_key = {
        (window.recipe_table.item(row, 0).text(), window.recipe_table.item(row, 1).text()): row
        for row in range(window.recipe_table.rowCount())
    }
    edits = {
        ("recipe", "name"): "edited_recipe",
        ("initial", "monomer"): "3.5",
        ("feed", "rate"): "0.42",
        ("integration", "t_final"): "9.5",
        ("integration", "output_points"): "33",
        ("integration", "backend"): "galerkin",
        ("integration", "galerkin_cells"): "12",
        ("reactor", "stages"): "6",
        ("heat", "enabled"): "true",
    }
    for key, value in edits.items():
        window.recipe_table.item(row_by_key[key], 2).setText(value)

    window._apply_recipe_table_edits()

    assert window.project.recipe.name == "edited_recipe"
    assert window.project.recipe.initial.monomer == 3.5
    assert window.project.recipe.feed.rate == 0.42
    assert window.project.recipe.integration.t_final == 9.5
    assert window.project.recipe.integration.output_points == 33
    assert window.project.recipe.integration.backend == "galerkin"
    assert window.project.recipe.integration.galerkin_cells == 12
    assert window.project.reactor.stages == 6
    assert window.project.heat_balance.enabled
    assert window.monomer.value() == 3.5
    assert window.feed_rate.value() == 0.42
    assert window.backend.currentText() == "galerkin"
    window._undo_project_edit()
    assert window.project.recipe.name == "default"
    window.close()
    app.processEvents()


def test_main_window_recipe_table_applies_profile_and_schedule_rows():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.project = set_temperature_profile(window.project, [(0.0, 300.0), (2.0, 320.0)])
    window.project = set_pressure_profile(window.project, [(0.0, 1.0)])
    window.project = append_pre_schedule_step(window.project, 1.0, "set_feed_rate", rate=0.2)
    window.project = append_pre_schedule_step(window.project, 2.0, "set_temperature", value=330.0)
    window._populate_recipe_table()
    row_by_key = {
        (window.recipe_table.item(row, 0).text(), window.recipe_table.item(row, 1).text()): row
        for row in range(window.recipe_table.rowCount())
    }

    window.recipe_table.item(row_by_key[("temperature_profile[1]", "time")], 2).setText("3.0")
    window.recipe_table.item(row_by_key[("temperature_profile[1]", "value")], 2).setText("335.0")
    window.recipe_table.item(row_by_key[("pressure_profile[0]", "value")], 2).setText("2.5")
    window.recipe_table.item(row_by_key[("pre_schedule[0]", "time")], 2).setText("1.5")
    window.recipe_table.item(row_by_key[("pre_schedule[0]", "rate")], 2).setText("0.45")
    window.recipe_table.item(row_by_key[("pre_schedule[1]", "value")], 2).setText("350.0")

    window._apply_recipe_table_edits()

    assert window.project.recipe.temperature_profile[1].time == 3.0
    assert window.project.recipe.temperature_profile[1].value == 335.0
    assert window.project.recipe.pressure_profile[0].value == 2.5
    assert window.project.recipe.pre_schedule[0]["time"] == 1.5
    assert window.project.recipe.pre_schedule[0]["rate"] == 0.45
    assert window.project.recipe.pre_schedule[1]["value"] == 350.0
    window._undo_project_edit()
    assert window.project.recipe.temperature_profile[1].value == 320.0
    window.close()
    app.processEvents()


def test_main_window_recipe_schedule_action_widgets_add_all_supported_actions():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    actions = {
        "set_feed_rate": ("rate", 0.21),
        "set_temperature": ("value", 330.0),
        "set_pressure": ("pressure", 3.5),
        "set_residence_time": ("value", 2.2),
        "set_coolant_temperature": ("value", 305.0),
        "set_additional_heat": ("heat", 4.0),
    }

    for index, (action, (_key, value)) in enumerate(actions.items(), start=1):
        window.schedule_action_selector.setCurrentText(action)
        window.schedule_time.setValue(float(index))
        window.schedule_value.setValue(value)
        window._add_schedule_action_from_widgets()

    by_action = {step["action"]: step for step in window.project.recipe.pre_schedule}
    values = {
        (window.recipe_table.item(row, 0).text(), window.recipe_table.item(row, 1).text()): window.recipe_table.item(row, 2).text()
        for row in range(window.recipe_table.rowCount())
    }

    assert len(window.project.recipe.pre_schedule) == len(actions)
    for action, (key, value) in actions.items():
        assert by_action[action][key] == value
    assert values[("profile", "pre_schedule_steps")] == "6"
    assert any(key[1] == "coolant_temperature" for key in values)
    assert any(key[1] == "heat" for key in values)
    window._undo_project_edit()
    assert len(window.project.recipe.pre_schedule) == 5
    window.close()
    app.processEvents()


def test_main_window_recipe_table_applies_feed_tank_rows():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.project = add_feed_tank(window.project, monomer=4.0, initiator=0.25, radicals=0.0, rate=0.12)
    window._populate_recipe_table()
    row_by_key = {
        (window.recipe_table.item(row, 0).text(), window.recipe_table.item(row, 1).text()): row
        for row in range(window.recipe_table.rowCount())
    }

    window.recipe_table.item(row_by_key[("feed_tank[0]", "monomer")], 2).setText("5.0")
    window.recipe_table.item(row_by_key[("feed_tank[0]", "rate")], 2).setText("0.25")
    window._apply_recipe_table_edits()

    assert window.project.recipe.feed_tanks[0].monomer == 5.0
    assert window.project.recipe.feed_tanks[0].rate == 0.25
    window._undo_project_edit()
    assert window.project.recipe.feed_tanks[0].rate == 0.12
    window.close()
    app.processEvents()


def test_main_window_recipe_table_applies_polymer_feed_rows():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.project = add_polymer_feed(window.project, name="seed", rate=0.05, mass_fraction=0.3, mn=1000.0, mw=1500.0)
    window._populate_recipe_table()
    row_by_key = {
        (window.recipe_table.item(row, 0).text(), window.recipe_table.item(row, 1).text()): row
        for row in range(window.recipe_table.rowCount())
    }

    window.recipe_table.item(row_by_key[("polymer_feed[0]", "rate")], 2).setText("0.08")
    window.recipe_table.item(row_by_key[("polymer_feed[0]", "Mw")], 2).setText("2000.0")
    window._apply_recipe_table_edits()

    assert window.project.recipe.polymer_feed[0]["name"] == "seed"
    assert window.project.recipe.polymer_feed[0]["rate"] == 0.08
    assert window.project.recipe.polymer_feed[0]["Mw"] == 2000.0
    window.close()
    app.processEvents()


def test_main_window_fitting_panel_runs_backend():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window._fit_gpkp_to_current_mass()

    assert window.fitting_result_table.rowCount() >= 4
    assert window.fitting_result_table.item(0, 0).text() == "success"
    window._global_search_gpkp_to_current_mass()
    assert window.fitting_result_table.rowCount() >= 4
    window._bayesian_sample_gpkp_to_current_mass()
    result_fields = {
        window.fitting_result_table.item(row, 0).text()
        for row in range(window.fitting_result_table.rowCount())
    }
    assert {"samples", "acceptance_rate", "GP_kp_mean", "GP_kp_ci95_low", "GP_kp_ci95_high"} <= result_fields
    window.close()
    app.processEvents()


def test_main_window_multi_experiment_fitting_panel_runs_backend():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    true_kp = window.project.kinetics.kp * 1.4
    for row, t_final in enumerate((1.5, 2.5)):
        case = window._project_with_t_final(t_final, required_outputs=("mass",))
        target_project = Project(
            reactor=case.reactor,
            kinetics=case.kinetics,
            recipe=case.recipe,
            outputs=case.outputs,
            heat_balance=case.heat_balance,
            substances=list(case.substances),
            polymers=list(case.polymers),
            reaction_steps=list(case.reaction_steps),
            generic_parameters={"GP_kp": true_kp},
        )
        target = compute_generic_outputs(SimulationEngine(target_project).run(), target_project.outputs)["mass"]
        window.fitting_experiment_table.item(row, 1).setText(str(t_final))
        window.fitting_experiment_table.item(row, 3).setText(f"{target:.12g}")

    window._multi_experiment_fit_gpkp()

    result_values = {
        window.fitting_result_table.item(row, 0).text(): window.fitting_result_table.item(row, 1).text()
        for row in range(window.fitting_result_table.rowCount())
    }
    assert result_values["success"] == "True"
    assert result_values["experiments"] == "2"
    assert abs(float(result_values["GP_kp"]) - true_kp) < 1e-3
    window.close()
    app.processEvents()


def test_main_window_scripted_output_editor_updates_project_outputs():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    window._add_scripted_output()
    window.script_output_table.item(0, 0).setText("mw_over_mn")
    window.script_output_table.item(0, 1).setText("Mw / max(Mn, 1e-12)")
    window._apply_scripted_outputs_from_table()
    window._run_simulation()

    assert "mw_over_mn" in window.project.outputs.enabled_generic_outputs
    assert window.project.outputs.scripted_outputs["mw_over_mn"] == "Mw / max(Mn, 1e-12)"
    assert any(window.output_table.item(row, 0).text() == "mw_over_mn" for row in range(window.output_table.rowCount()))
    window.close()
    app.processEvents()


def test_main_window_scripted_output_editor_accepts_loop_script():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    script = "values = [Mn, Mw, Mz]\nresult = 0\nfor i in range(3):\n    result += values[i]\n"

    window._add_scripted_output()
    window.script_output_table.item(0, 0).setText("moment_sum")
    window.script_output_table.item(0, 1).setText(script)
    window._apply_scripted_outputs_from_table()
    window._run_simulation()

    assert window.project.outputs.scripted_outputs["moment_sum"] == script.strip()
    assert any(window.output_table.item(row, 0).text() == "moment_sum" for row in range(window.output_table.rowCount()))
    window.close()
    app.processEvents()


def test_main_window_undo_restores_scripted_outputs():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    original_outputs = window.project.outputs.enabled_generic_outputs
    window._add_scripted_output()
    window.script_output_table.item(0, 0).setText("mw_over_mn")
    window.script_output_table.item(0, 1).setText("Mw / max(Mn, 1e-12)")
    window._apply_scripted_outputs_from_table()
    assert "mw_over_mn" in window.project.outputs.enabled_generic_outputs

    window._undo_project_edit()

    assert window.project.outputs.enabled_generic_outputs == original_outputs
    assert "mw_over_mn" not in window.project.outputs.scripted_outputs
    window.close()
    app.processEvents()


def test_main_window_can_save_current_result_manifest(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    manifest = window._save_result_to_directory(tmp_path / "run_gui")

    assert manifest.exists()
    assert (tmp_path / "run_gui" / "distribution_history.npz").exists()
    assert (tmp_path / "run_gui" / "moments.csv").exists()
    window.close()
    app.processEvents()


def test_main_window_sample_recent_and_png_pdf_exports(tmp_path, monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    window.settings.clear()
    window.recent_project_paths = []
    window._refresh_recent_project_actions()

    project_path = tmp_path / "sample.predici.json"
    window._save_project_to_path(project_path)
    assert window.recent_project_paths[0] == project_path
    assert window.recent_menu.actions()[0].text() == project_path.name

    window._open_sample_project()
    assert window.current_project_path is None
    assert window.project.reactor.kind == window.reactor_kind.currentText()

    png_path = tmp_path / "distribution.png"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(png_path), "PNG (*.png)"))
    window._save_report()
    assert png_path.exists()

    pdf_path = tmp_path / "distribution.pdf"
    monkeypatch.setattr(QFileDialog, "getSaveFileName", lambda *args, **kwargs: (str(pdf_path), "PDF (*.pdf)"))
    window._save_report()
    assert pdf_path.exists()

    window.close()
    app.processEvents()
