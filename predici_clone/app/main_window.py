from __future__ import annotations

from pathlib import Path

import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PySide6.QtCore import QSettings, Qt, QThread
from PySide6.QtGui import QAction, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
    QDockWidget,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QDoubleSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from predici_clone.api import (
    FRPParameters,
    FeedStream,
    InitialConditions,
    IntegrationControl,
    OutputConfig,
    Parameter,
    PolymerSpecies,
    Project,
    ProfilePoint,
    ReactorConfig,
    RecipeComponent,
    Recipe,
    Substance,
    add_parameter,
    add_polymer_species,
    add_substance,
    append_pre_schedule_step,
    consistency_sum,
    fill_remainder,
    load_project,
    make_concentration_consistent,
    normalize_recipe_components,
    save_simulation_result,
    save_project,
)
from predici_clone.api.project_schema import sample_project
from predici_clone.api.validation import validate_project, validation_summary
from predici_clone.app.workers.simulation_worker import SimulationWorker
from predici_clone.core.moments import MomentReport, from_discrete_distribution
from predici_clone.engine import SimulationEngine
from predici_clone.engine.simulation_result import SimulationResult
from predici_clone.kinetics import RateLaw, ReactionKind, ReactionStep
from predici_clone.kinetics.reaction_builder import build_polymer_reaction_step, reaction_pattern_catalog
from predici_clone.postprocess.generic_outputs import generic_outputs_frame
from predici_clone.postprocess.scripted_outputs import evaluate_script_scope
from predici_clone.postprocess.distribution_plot import save_distribution_plot
from predici_clone.postprocess.gpc import distribution_to_gpc_profile
from predici_clone.postprocess.moments_report import report_frame, write_distribution_report
from predici_clone.postprocess.experiment_data import (
    DataMapping,
    ExperimentDataset,
    load_experiment_csv,
    residual_frame,
    trim_experiment,
)
from predici_clone.postprocess.parameter_estimation import (
    FittingExperiment,
    FittingProblem,
    MultiExperimentFittingProblem,
    OutputTarget,
    ParameterSpec,
    fit_generic_parameters,
    fit_multi_experiment_generic_parameters,
    global_search_generic_parameters,
    sample_bayesian_posterior,
    sample_multi_experiment_bayesian_posterior,
)
from predici_clone.script import ScriptCommandState, generate_script_template, parse_reaction_rate_modifier, script_command_namespace, script_function_catalog
from predici_clone.validation.paper_benchmarks import available_cases


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("PREDICI Clone")
        self.current_distribution = np.zeros(1)
        self.current_first_length = 0
        self.current_explicit_lengths: np.ndarray | None = None
        self.current_result: SimulationResult | None = None
        self.current_time_index = -1
        self.mwd_overlays: list[dict[str, object]] = []
        self.project = Project()
        self.current_project_path: Path | None = None
        self._thread: QThread | None = None
        self._worker: SimulationWorker | None = None
        self._undo_stack: list[dict] = []
        self._redo_stack: list[dict] = []
        self.settings = QSettings("PrediciClone", "PrediciClone")
        self.recent_project_paths = self._load_recent_project_paths()

        self._create_actions()
        self._create_menus()
        self._create_toolbar()
        self._create_statusbar()
        self._create_central_tabs()
        self._create_docks()
        self._apply_stylesheet()
        self._populate_project_tree()
        self._sync_controls_from_project(self.project)
        self._update_undo_redo_actions()

        self._run_simulation()

    def _create_actions(self) -> None:
        self.run_action = QAction("Run", self)
        self.run_action.triggered.connect(self._start_simulation_worker)
        self.stop_action = QAction("Stop", self)
        self.stop_action.triggered.connect(self._request_stop)
        self.open_project_action = QAction("Open Project", self)
        self.open_project_action.triggered.connect(self._open_project_dialog)
        self.save_project_action = QAction("Save Project", self)
        self.save_project_action.triggered.connect(self._save_project_dialog)
        self.save_result_action = QAction("Save Result", self)
        self.save_result_action.triggered.connect(self._save_result_dialog)
        self.new_sample_project_action = QAction("Sample Project", self)
        self.new_sample_project_action.triggered.connect(self._open_sample_project)
        self.save_action = QAction("Export Chart/Data", self)
        self.save_action.triggered.connect(self._save_report)
        self.load_benchmark_action = QAction("Load Benchmark", self)
        self.load_benchmark_action.triggered.connect(self._load_benchmark)
        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.triggered.connect(self._undo_project_edit)
        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.triggered.connect(self._redo_project_edit)

    def _create_menus(self) -> None:
        file_menu = self.menuBar().addMenu("File")
        file_menu.addAction(self.new_sample_project_action)
        file_menu.addSeparator()
        file_menu.addAction(self.open_project_action)
        file_menu.addAction(self.save_project_action)
        file_menu.addAction(self.save_result_action)
        self.recent_menu = QMenu("Recent Projects", self)
        file_menu.addMenu(self.recent_menu)
        file_menu.addSeparator()
        file_menu.addAction(self.save_action)
        self._refresh_recent_project_actions()
        edit_menu = self.menuBar().addMenu("Edit")
        edit_menu.addAction(self.undo_action)
        edit_menu.addAction(self.redo_action)
        model_menu = self.menuBar().addMenu("Model")
        model_menu.addAction(self.load_benchmark_action)
        simulate_menu = self.menuBar().addMenu("Simulate")
        simulate_menu.addAction(self.run_action)
        simulate_menu.addAction(self.stop_action)
        self.menuBar().addMenu("Analysis")
        self.menuBar().addMenu("Fitting")
        self.menuBar().addMenu("Help")

    def _create_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        toolbar.addAction(self.run_action)
        toolbar.addAction(self.stop_action)
        toolbar.addSeparator()
        toolbar.addAction(self.open_project_action)
        toolbar.addAction(self.new_sample_project_action)
        toolbar.addAction(self.save_project_action)
        toolbar.addAction(self.save_result_action)
        toolbar.addSeparator()
        toolbar.addAction(self.undo_action)
        toolbar.addAction(self.redo_action)
        toolbar.addSeparator()
        toolbar.addAction(self.save_action)
        toolbar.addAction(self.load_benchmark_action)
        self.addToolBar(toolbar)

    def _create_statusbar(self) -> None:
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setFixedWidth(180)
        self.statusBar().addPermanentWidget(self.progress)
        self.statusBar().showMessage("Ready")

    def _create_central_tabs(self) -> None:
        self.tabs = QTabWidget()
        self.dashboard_tab = self._build_dashboard_tab()
        self.simulation_tab = self._build_simulation_tab()
        self.mwd_tab = self._build_mwd_tab()
        self.model_builder_tab = self._build_model_builder_tab()
        self.component_tab = self._build_component_tab()
        self.recipe_tab = self._build_recipe_tab()
        self.fitting_tab = self._build_fitting_tab()
        self.script_tab = self._build_script_tab()

        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        self.tabs.addTab(self.model_builder_tab, "Model Builder")
        self.tabs.addTab(self.component_tab, "Components")
        self.tabs.addTab(self.recipe_tab, "Recipe")
        self.tabs.addTab(self.simulation_tab, "Simulation")
        self.tabs.addTab(self.mwd_tab, "MWD Viewer")
        self.tabs.addTab(self.fitting_tab, "Fitting")
        self.tabs.addTab(self.script_tab, "Script")
        self.setCentralWidget(self.tabs)

    def _create_docks(self) -> None:
        project_dock = QDockWidget("Project", self)
        self.project_tree = QTreeWidget()
        self.project_tree.setHeaderHidden(True)
        project_dock.setWidget(self.project_tree)
        self.addDockWidget(Qt.LeftDockWidgetArea, project_dock)

        inspector_dock = QDockWidget("Inspector", self)
        self.inspector = QTableWidget(0, 2)
        self.inspector.setHorizontalHeaderLabels(["Property", "Value"])
        self.inspector.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        inspector_dock.setWidget(self.inspector)
        self.addDockWidget(Qt.RightDockWidgetArea, inspector_dock)

        log_dock = QDockWidget("Log", self)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        log_dock.setWidget(self.log)
        self.addDockWidget(Qt.BottomDockWidgetArea, log_dock)

    def _build_dashboard_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.dashboard_summary = QLabel()
        self.dashboard_summary.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.dashboard_summary.setObjectName("DashboardSummary")
        self.output_table = QTableWidget(0, 2)
        self.output_table.setHorizontalHeaderLabels(["Output", "Value"])
        self.output_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.dashboard_summary)
        layout.addWidget(self.output_table)
        return page

    def _build_simulation_tab(self) -> QWidget:
        page = QWidget()
        layout = QHBoxLayout(page)
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._build_controls())
        splitter.addWidget(self._build_live_table())
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter)
        return page

    def _build_model_builder_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        buttons = QHBoxLayout()
        self.reaction_kind_selector = QComboBox()
        self.reaction_kind_selector.addItems([kind.value for kind in ReactionKind])
        self.reaction_pattern_selector = QComboBox()
        self.reaction_pattern_selector.addItems([pattern.name for pattern in reaction_pattern_catalog() if pattern.kind is not None])
        self.reaction_pattern_selector.currentTextChanged.connect(self._update_reaction_pattern_preview)
        self.reaction_pattern_selector.currentTextChanged.connect(self._populate_reaction_pattern_slots)
        add = QPushButton("Add Reaction")
        add.clicked.connect(self._add_selected_reaction_step)
        add_pattern = QPushButton("Add Pattern")
        add_pattern.clicked.connect(self._add_selected_reaction_pattern)
        remove = QPushButton("Remove Selected")
        remove.clicked.connect(self._remove_selected_reaction_step)
        apply = QPushButton("Apply Table Edits")
        apply.clicked.connect(self._apply_reaction_table_edits)
        self.reaction_modifier_expression = QComboBox()
        self.reaction_modifier_expression.setEditable(True)
        self.reaction_modifier_expression.addItems(["GP_kp(File)", "GP_kp*File", "GP_kt(File)"])
        self.reaction_modifier_script = QPlainTextEdit()
        self.reaction_modifier_script.setPlainText('result = getkp("GP_kp")')
        self.reaction_modifier_script.setMaximumHeight(72)
        apply_modifier = QPushButton("Apply Modifier")
        apply_modifier.clicked.connect(self._apply_reaction_modifier_to_selected_step)
        buttons.addWidget(self.reaction_kind_selector)
        buttons.addWidget(add)
        buttons.addWidget(self.reaction_pattern_selector)
        buttons.addWidget(add_pattern)
        buttons.addWidget(remove)
        buttons.addWidget(apply)
        buttons.addStretch(1)
        modifier_buttons = QHBoxLayout()
        modifier_buttons.addWidget(QLabel("Modifier"))
        modifier_buttons.addWidget(self.reaction_modifier_expression)
        modifier_buttons.addWidget(apply_modifier)
        self.reaction_table = QTableWidget(0, 7)
        self.reaction_table.setHorizontalHeaderLabels(["enabled", "name", "kind", "site", "reactants", "products", "rate"])
        self.reaction_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.reaction_pattern_preview = QLabel()
        self.reaction_pattern_preview.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.reaction_pattern_catalog_table = QTableWidget(0, 8)
        self.reaction_pattern_catalog_table.setHorizontalHeaderLabels(
            ["name", "category", "kind", "reactants", "products", "parameters", "flow", "description"]
        )
        self.reaction_pattern_catalog_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.reaction_pattern_catalog_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.reaction_pattern_slot_table = QTableWidget(0, 3)
        self.reaction_pattern_slot_table.setHorizontalHeaderLabels(["type", "slot", "value"])
        self.reaction_pattern_slot_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addLayout(buttons)
        layout.addWidget(self.reaction_pattern_preview)
        layout.addWidget(self.reaction_pattern_catalog_table)
        layout.addWidget(QLabel("Pattern slots"))
        layout.addWidget(self.reaction_pattern_slot_table)
        layout.addLayout(modifier_buttons)
        layout.addWidget(self.reaction_modifier_script)
        layout.addWidget(self.reaction_table)
        self._populate_reaction_pattern_catalog_table()
        self._update_reaction_pattern_preview()
        self._populate_reaction_pattern_slots()
        return page

    def _build_component_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        buttons = QHBoxLayout()
        add_substance = QPushButton("Add Substance")
        add_substance.clicked.connect(self._add_component_substance_row)
        add_polymer = QPushButton("Add Polymer")
        add_polymer.clicked.connect(self._add_component_polymer_row)
        add_parameter = QPushButton("Add Parameter")
        add_parameter.clicked.connect(self._add_component_parameter_row)
        apply = QPushButton("Apply Components")
        apply.clicked.connect(self._apply_component_tables)
        buttons.addWidget(add_substance)
        buttons.addWidget(add_polymer)
        buttons.addWidget(add_parameter)
        buttons.addWidget(apply)
        buttons.addStretch(1)
        self.substance_table = QTableWidget(0, 12)
        self.substance_table.setHorizontalHeaderLabels(
            ["name", "alias", "kind", "MW", "density", "monomer", "phase", "rho mode", "rho a", "rho b", "cp coeffs", "cp K"]
        )
        self.substance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.polymer_table = QTableWidget(0, 13)
        self.polymer_table.setHorizontalHeaderLabels(
            ["name", "alias", "base", "active", "dead", "MW", "density", "phase", "rho mode", "rho a", "rho b", "cp coeffs", "cp K"]
        )
        self.polymer_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.parameter_table = QTableWidget(0, 5)
        self.parameter_table.setHorizontalHeaderLabels(["name", "value", "unit", "kind", "Ea"])
        self.parameter_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addLayout(buttons)
        layout.addWidget(QLabel("Substances"))
        layout.addWidget(self.substance_table)
        layout.addWidget(QLabel("Polymer species"))
        layout.addWidget(self.polymer_table)
        layout.addWidget(QLabel("Parameters"))
        layout.addWidget(self.parameter_table)
        return page

    def _build_mwd_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.figure = Figure(figsize=(7, 5), tight_layout=True)
        self.canvas = FigureCanvas(self.figure)
        self.summary_label = QLabel()
        self.summary_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.mwd_time_label = QLabel("time: final")
        self.mwd_time_slider = QSlider(Qt.Horizontal)
        self.mwd_time_slider.setEnabled(False)
        self.mwd_time_slider.valueChanged.connect(self._show_mwd_time_index)
        self.mwd_mode_selector = QComboBox()
        self.mwd_mode_selector.addItems(["weight fraction", "mole fraction"])
        self.mwd_mode_selector.currentTextChanged.connect(self._redraw_current_distribution)
        self.mwd_axis_selector = QComboBox()
        self.mwd_axis_selector.addItems(["chain length", "molecular weight", "log molecular weight"])
        self.mwd_axis_selector.currentTextChanged.connect(self._redraw_current_distribution)
        self.mwd_gpc_toggle = QCheckBox("GPC convolution")
        self.mwd_gpc_toggle.toggled.connect(self._redraw_current_distribution)
        self.mwd_overlay_toggle = QCheckBox("Overlay previous/reference")
        self.mwd_overlay_toggle.setChecked(True)
        self.mwd_overlay_toggle.toggled.connect(self._redraw_current_distribution)
        self.clear_mwd_overlays_button = QPushButton("Clear Overlays")
        self.clear_mwd_overlays_button.clicked.connect(self._clear_mwd_overlays)
        self.moment_table = QTableWidget(0, 2)
        self.component_info_table = QTableWidget(0, 2)
        self.component_info_table.setHorizontalHeaderLabels(["field", "value"])
        self.component_info_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.component_info_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        add_chart_page = QPushButton("Add Chart")
        add_chart_page.clicked.connect(self._add_chart_page_row)
        add_chart_graph = QPushButton("Add Graph")
        add_chart_graph.clicked.connect(self._add_chart_graph_row)
        apply_charts = QPushButton("Apply Charts")
        apply_charts.clicked.connect(self._apply_chart_administration)
        self.chart_page_table = QTableWidget(0, 3)
        self.chart_page_table.setHorizontalHeaderLabels(["page", "title", "layout"])
        self.chart_page_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.chart_graph_table = QTableWidget(0, 7)
        self.chart_graph_table.setHorizontalHeaderLabels(["page", "graph", "mode", "y axis", "x axis", "scale", "source"])
        self.chart_graph_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        controls = QHBoxLayout()
        controls.addWidget(self.mwd_time_label)
        controls.addWidget(self.mwd_time_slider, 1)
        controls.addWidget(self.mwd_mode_selector)
        controls.addWidget(self.mwd_axis_selector)
        controls.addWidget(self.mwd_gpc_toggle)
        controls.addWidget(self.mwd_overlay_toggle)
        controls.addWidget(self.clear_mwd_overlays_button)
        layout.addWidget(self.canvas, 1)
        layout.addLayout(controls)
        layout.addWidget(self.summary_label)
        layout.addWidget(self.moment_table)
        layout.addWidget(QLabel("Components information"))
        layout.addWidget(self.component_info_table)
        chart_buttons = QHBoxLayout()
        chart_buttons.addWidget(add_chart_page)
        chart_buttons.addWidget(add_chart_graph)
        chart_buttons.addWidget(apply_charts)
        chart_buttons.addStretch(1)
        layout.addWidget(QLabel("Chart administration"))
        layout.addLayout(chart_buttons)
        layout.addWidget(self.chart_page_table)
        layout.addWidget(self.chart_graph_table)
        self._populate_chart_administration()
        return page

    def _build_recipe_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        self.recipe_table = QTableWidget(0, 3)
        self.recipe_table.setHorizontalHeaderLabels(["section", "field", "value"])
        self.recipe_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        refresh = QPushButton("Refresh From Controls")
        refresh.clicked.connect(self._refresh_recipe_table_from_controls)
        apply = QPushButton("Apply Table Edits")
        apply.clicked.connect(self._apply_recipe_table_edits)
        self.schedule_action_selector = QComboBox()
        self.schedule_action_selector.addItems(
            [
                "set_feed_rate",
                "set_temperature",
                "set_pressure",
                "set_residence_time",
                "set_coolant_temperature",
                "set_additional_heat",
            ]
        )
        self.schedule_time = self._double_spin(0.0, 100000.0, 1.0)
        self.schedule_value = self._double_spin(-1000000.0, 1000000.0, 0.0)
        add_schedule = QPushButton("Add Schedule Action")
        add_schedule.clicked.connect(self._add_schedule_action_from_widgets)
        add_consistency = QPushButton("Add Consistency Row")
        add_consistency.clicked.connect(self._add_recipe_consistency_row)
        normalize_recipe = QPushButton("Normalize Mode")
        normalize_recipe.clicked.connect(self._normalize_recipe_consistency_mode)
        set_concentration = QPushButton("Set Concentration Consistent")
        set_concentration.clicked.connect(self._set_recipe_concentration_consistent)
        set_rest = QPushButton("Set Rest")
        set_rest.clicked.connect(self._set_recipe_rest)
        buttons = QHBoxLayout()
        buttons.addWidget(refresh)
        buttons.addWidget(apply)
        buttons.addStretch(1)
        schedule_buttons = QHBoxLayout()
        schedule_buttons.addWidget(QLabel("Action"))
        schedule_buttons.addWidget(self.schedule_action_selector)
        schedule_buttons.addWidget(QLabel("Time"))
        schedule_buttons.addWidget(self.schedule_time)
        schedule_buttons.addWidget(QLabel("Value"))
        schedule_buttons.addWidget(self.schedule_value)
        schedule_buttons.addWidget(add_schedule)
        schedule_buttons.addStretch(1)
        consistency_buttons = QHBoxLayout()
        self.recipe_consistency_target = QComboBox()
        self.recipe_consistency_target.addItem("rest")
        self.recipe_input_mode = QComboBox()
        self.recipe_input_mode.addItems(
            [
                "absolute_mass",
                "mass_part_total_mass",
                "absolute_mole",
                "mole_part",
                "concentration_and_volume",
                "mass_part_total_mole",
                "mole_part_total_mass",
            ]
        )
        self.recipe_basis_volume = self._double_spin(0.0, 1000000.0, 1.0)
        self.recipe_basis_total_mass = self._double_spin(0.0, 1000000.0, 1.0)
        self.recipe_basis_total_moles = self._double_spin(0.0, 1000000.0, 1.0)
        consistency_buttons.addWidget(QLabel("Target"))
        consistency_buttons.addWidget(self.recipe_consistency_target)
        consistency_buttons.addWidget(QLabel("Input as"))
        consistency_buttons.addWidget(self.recipe_input_mode)
        consistency_buttons.addWidget(QLabel("Volume"))
        consistency_buttons.addWidget(self.recipe_basis_volume)
        consistency_buttons.addWidget(QLabel("Mass"))
        consistency_buttons.addWidget(self.recipe_basis_total_mass)
        consistency_buttons.addWidget(QLabel("Moles"))
        consistency_buttons.addWidget(self.recipe_basis_total_moles)
        consistency_buttons.addWidget(add_consistency)
        consistency_buttons.addWidget(normalize_recipe)
        consistency_buttons.addWidget(set_concentration)
        consistency_buttons.addWidget(set_rest)
        consistency_buttons.addStretch(1)
        self.recipe_consistency_sum = QLabel("sum: 0")
        self.recipe_consistency_table = QTableWidget(0, 8)
        self.recipe_consistency_table.setHorizontalHeaderLabels(
            ["name", "MW", "density", "mass", "moles", "concentration", "mass part", "mole part"]
        )
        self.recipe_consistency_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addLayout(buttons)
        layout.addLayout(schedule_buttons)
        layout.addWidget(self.recipe_table)
        layout.addWidget(QLabel("Consistency"))
        layout.addLayout(consistency_buttons)
        layout.addWidget(self.recipe_consistency_sum)
        layout.addWidget(self.recipe_consistency_table)
        return page

    def _build_fitting_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        run_fit = QPushButton("Local Fit GP_kp")
        run_fit.clicked.connect(self._fit_gpkp_to_current_mass)
        run_global = QPushButton("Global Search GP_kp")
        run_global.clicked.connect(self._global_search_gpkp_to_current_mass)
        run_bayes = QPushButton("Bayesian Sample GP_kp")
        run_bayes.clicked.connect(self._bayesian_sample_gpkp_to_current_mass)
        run_multi = QPushButton("Multi-Experiment Fit")
        run_multi.clicked.connect(self._multi_experiment_fit_gpkp)
        run_multi_bayes = QPushButton("Bayesian Multi-Experiment")
        run_multi_bayes.clicked.connect(self._multi_experiment_bayesian_sample)
        load_csv = QPushButton("Load Residual CSV")
        load_csv.clicked.connect(self._load_residual_csv_dialog)
        eval_residuals = QPushButton("Evaluate Residuals")
        eval_residuals.clicked.connect(self._evaluate_loaded_residuals)
        add_mapping = QPushButton("Add Mapping")
        add_mapping.clicked.connect(self._add_residual_mapping_row)
        remove_mapping = QPushButton("Remove Mapping")
        remove_mapping.clicked.connect(self._remove_selected_residual_mapping_row)
        add_parameter = QPushButton("Add Parameter")
        add_parameter.clicked.connect(self._add_fitting_parameter_row)
        remove_parameter = QPushButton("Remove Parameter")
        remove_parameter.clicked.connect(self._remove_selected_fitting_parameter_row)
        self.fitting_parameter_table = QTableWidget(1, 5)
        self.fitting_parameter_table.setHorizontalHeaderLabels(["name", "initial", "lower", "upper", "fixed"])
        for column, value in enumerate(["GP_kp", "0.08", "0.001", "1.0", "False"]):
            self.fitting_parameter_table.setItem(0, column, QTableWidgetItem(value))
        self.fitting_target_table = QTableWidget(1, 3)
        self.fitting_target_table.setHorizontalHeaderLabels(["output", "target", "weight"])
        for column, value in enumerate(["mass", "0", "100000"]):
            self.fitting_target_table.setItem(0, column, QTableWidgetItem(value))
        self.fitting_experiment_table = QTableWidget(2, 5)
        self.fitting_experiment_table.setHorizontalHeaderLabels(["experiment", "t_final", "output", "target", "weight"])
        for row, values in enumerate((("exp_1", "1.5", "mass", "0", "100000"), ("exp_2", "2.5", "mass", "0", "100000"))):
            for column, value in enumerate(values):
                self.fitting_experiment_table.setItem(row, column, QTableWidgetItem(value))
        self.fitting_result_table = QTableWidget(0, 2)
        self.fitting_result_table.setHorizontalHeaderLabels(["field", "value"])
        self.fitting_residual_table = QTableWidget(0, 7)
        self.fitting_residual_table.setHorizontalHeaderLabels(
            ["experiment", "time", "output", "observed", "model", "weight", "residual"]
        )
        self.fitting_residual_mapping_table = QTableWidget(1, 5)
        self.fitting_residual_mapping_table.setHorizontalHeaderLabels(["output", "column", "weight", "start", "end"])
        for column, value in enumerate(["mass", "mass_obs", "1.0", "", ""]):
            self.fitting_residual_mapping_table.setItem(0, column, QTableWidgetItem(value))
        self.fitting_residual_figure = Figure(figsize=(6, 3), tight_layout=True)
        self.fitting_residual_canvas = FigureCanvas(self.fitting_residual_figure)
        self.fitting_residual_dataset: ExperimentDataset | None = None
        self.fitting_raw_residual_dataset: ExperimentDataset | None = None
        buttons = QHBoxLayout()
        buttons.addWidget(run_fit)
        buttons.addWidget(run_global)
        buttons.addWidget(run_bayes)
        buttons.addWidget(run_multi)
        buttons.addWidget(run_multi_bayes)
        buttons.addWidget(load_csv)
        buttons.addWidget(eval_residuals)
        buttons.addStretch(1)
        layout.addLayout(buttons)
        parameter_buttons = QHBoxLayout()
        parameter_buttons.addWidget(add_parameter)
        parameter_buttons.addWidget(remove_parameter)
        parameter_buttons.addStretch(1)
        layout.addWidget(QLabel("Parameters"))
        layout.addLayout(parameter_buttons)
        layout.addWidget(self.fitting_parameter_table)
        layout.addWidget(QLabel("Targets"))
        layout.addWidget(self.fitting_target_table)
        layout.addWidget(QLabel("Experiments"))
        layout.addWidget(self.fitting_experiment_table)
        layout.addWidget(QLabel("Result"))
        layout.addWidget(self.fitting_result_table)
        layout.addWidget(QLabel("Residuals"))
        mapping_buttons = QHBoxLayout()
        mapping_buttons.addWidget(add_mapping)
        mapping_buttons.addWidget(remove_mapping)
        mapping_buttons.addStretch(1)
        layout.addLayout(mapping_buttons)
        layout.addWidget(self.fitting_residual_mapping_table)
        layout.addWidget(self.fitting_residual_canvas, 1)
        layout.addWidget(self.fitting_residual_table)
        return page

    def _build_script_tab(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        buttons = QHBoxLayout()
        add = QPushButton("Add Scripted Output")
        add.clicked.connect(self._add_scripted_output)
        template = QPushButton("Generate Template")
        template.clicked.connect(self._generate_script_template_row)
        apply = QPushButton("Apply Scripted Outputs")
        apply.clicked.connect(self._apply_scripted_outputs_from_table)
        add_debug = QPushButton("Add Debug Script")
        add_debug.clicked.connect(self._add_debug_script_row)
        remove_debug = QPushButton("Remove Debug Script")
        remove_debug.clicked.connect(self._remove_selected_debug_script_row)
        run_debug = QPushButton("Run Debug")
        run_debug.clicked.connect(self._run_debug_scripts)
        move_debug = QPushButton("Move Trace")
        move_debug.clicked.connect(self._move_debug_trace_to_window)
        buttons.addWidget(add)
        buttons.addWidget(template)
        buttons.addWidget(apply)
        buttons.addWidget(add_debug)
        buttons.addWidget(remove_debug)
        buttons.addWidget(run_debug)
        buttons.addWidget(move_debug)
        buttons.addStretch(1)
        self.script_output_table = QTableWidget(0, 2)
        self.script_output_table.setHorizontalHeaderLabels(["name", "expression"])
        self.script_output_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.debug_script_table = QTableWidget(0, 2)
        self.debug_script_table.setHorizontalHeaderLabels(["name", "script"])
        self.debug_script_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.debug_trace_table = QTableWidget(0, 5)
        self.debug_trace_table.setHorizontalHeaderLabels(["script", "line", "text", "assignment", "value"])
        self.debug_trace_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.debug_trace_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.script_function_table = QTableWidget(0, 5)
        self.script_function_table.setHorizontalHeaderLabels(["name", "args", "category", "status", "description"])
        self.script_function_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.script_function_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addLayout(buttons)
        layout.addWidget(self.script_output_table)
        layout.addWidget(QLabel("Debug scripts"))
        layout.addWidget(self.debug_script_table)
        layout.addWidget(QLabel("Debug trace"))
        layout.addWidget(self.debug_trace_table)
        layout.addWidget(QLabel("Function catalog"))
        layout.addWidget(self.script_function_table)
        self._populate_script_function_catalog()
        return page

    def _build_controls(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        reactor_box = QGroupBox("Scenario")
        form = QFormLayout(reactor_box)
        self.reactor_kind = QComboBox()
        self.reactor_kind.addItems(["Batch", "Semi-batch", "CSTR", "Cascade", "PFR"])
        self.nmax = self._spin(20, 10000, 120)
        self.t_final = self._double_spin(0.1, 10000.0, 30.0)
        self.kp = self._double_spin(0.0, 100.0, 0.08)
        self.kt = self._double_spin(0.0, 100.0, 0.05)
        self.kd = self._double_spin(0.0, 100.0, 0.02)
        self.monomer = self._double_spin(0.0, 1000.0, 2.0)
        self.initiator = self._double_spin(0.0, 1000.0, 0.15)
        self.feed_rate = self._double_spin(0.0, 1000.0, 0.06)
        self.residence_time = self._double_spin(0.01, 10000.0, 8.0)
        self.stages = self._spin(1, 200, 4)
        self.axial_cells = self._spin(1, 500, 12)
        self.backend = QComboBox()
        self.backend.addItems(["discrete", "galerkin", "galerkin_direct"])
        self.simulation_mode = QComboBox()
        self.simulation_mode.addItems(["distributions", "moments"])
        self.include_monte_carlo = QCheckBox("incl. Monte Carlo method")
        self.use_tau_leaping = QCheckBox("use tau leaping")
        self.galerkin_cells = self._spin(1, 200, 8)
        self.galerkin_degree = self._spin(0, 8, 2)
        for label, widget in [
            ("reactor", self.reactor_kind),
            ("backend", self.backend),
            ("simulation mode", self.simulation_mode),
            ("n max", self.nmax),
            ("time", self.t_final),
            ("kp", self.kp),
            ("kt", self.kt),
            ("kd", self.kd),
            ("monomer", self.monomer),
            ("initiator", self.initiator),
            ("feed rate", self.feed_rate),
            ("residence time", self.residence_time),
            ("cascade stages", self.stages),
            ("PFR axial cells", self.axial_cells),
            ("Galerkin cells", self.galerkin_cells),
            ("Galerkin degree", self.galerkin_degree),
        ]:
            form.addRow(label, widget)
        form.addRow("", self.include_monte_carlo)
        form.addRow("", self.use_tau_leaping)
        layout.addWidget(reactor_box)

        benchmark_box = QGroupBox("Benchmarks")
        benchmark_layout = QVBoxLayout(benchmark_box)
        self.benchmark_combo = QComboBox()
        self.benchmark_cases = available_cases()
        self.benchmark_combo.addItems([case.name for case in self.benchmark_cases])
        benchmark_layout.addWidget(self.benchmark_combo)
        layout.addWidget(benchmark_box)

        buttons = QHBoxLayout()
        run = QPushButton("Run")
        run.clicked.connect(self._start_simulation_worker)
        self.run_to_time_input = self._double_spin(0.0, 10000.0, 1.0)
        run_to_time = QPushButton("Proc")
        run_to_time.clicked.connect(self._run_to_time_from_controls)
        single_step = QPushButton("1 Step")
        single_step.clicked.connect(self._single_step_from_controls)
        load = QPushButton("Benchmark")
        load.clicked.connect(self._load_benchmark)
        save = QPushButton("Save CSV")
        save.clicked.connect(self._save_report)
        buttons.addWidget(run)
        buttons.addWidget(QLabel("End time"))
        buttons.addWidget(self.run_to_time_input)
        buttons.addWidget(run_to_time)
        buttons.addWidget(single_step)
        buttons.addWidget(load)
        buttons.addWidget(save)
        layout.addLayout(buttons)
        layout.addStretch(1)
        return panel

    def _build_live_table(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)
        self.live_table = QTableWidget(0, 4)
        self.live_table.setHorizontalHeaderLabels(["time", "Mn", "Mw", "PDI"])
        self.live_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.live_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.actual_values_table = QTableWidget(0, 4)
        self.actual_values_table.setHorizontalHeaderLabels(["step", "time", "stepsize", "variables"])
        self.actual_values_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.actual_values_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.live_table)
        layout.addWidget(QLabel("Actual values"))
        layout.addWidget(self.actual_values_table)
        return panel

    def _project_from_controls(self) -> Project:
        return Project(
            schema_version=self.project.schema_version,
            name=self.project.name,
            reactor=ReactorConfig(
                kind=self.reactor_kind.currentText(),
                nmax=self.nmax.value(),
                volume=1.0,
                residence_time=self.residence_time.value(),
                stages=self.stages.value(),
                axial_cells=self.axial_cells.value(),
            ),
            kinetics=FRPParameters(kp=self.kp.value(), kt=self.kt.value(), kd=self.kd.value(), initiator_efficiency=0.6),
            recipe=Recipe(
                name=self.project.recipe.name,
                unit_system=self.project.recipe.unit_system,
                initial=InitialConditions(monomer=self.monomer.value(), initiator=self.initiator.value()),
                feed=FeedStream(monomer=self.monomer.value(), initiator=self.initiator.value(), rate=self.feed_rate.value()),
                feed_tanks=list(self.project.recipe.feed_tanks),
                polymer_feed=list(self.project.recipe.polymer_feed),
                integration=IntegrationControl(
                    t_final=self.t_final.value(),
                    output_points=80,
                    backend=self.backend.currentText(),
                    galerkin_cells=self.galerkin_cells.value(),
                    galerkin_degree=self.galerkin_degree.value(),
                    simulation_mode=self.simulation_mode.currentText(),
                    include_monte_carlo=self.include_monte_carlo.isChecked(),
                    use_tau_leaping=self.use_tau_leaping.isChecked(),
                ),
                pre_schedule=list(self.project.recipe.pre_schedule),
                temperature_profile=list(self.project.recipe.temperature_profile),
                pressure_profile=list(self.project.recipe.pressure_profile),
                shooting_control=dict(self.project.recipe.shooting_control),
            ),
            outputs=self.project.outputs,
            heat_balance=self.project.heat_balance,
            substances=list(self.project.substances),
            polymers=list(self.project.polymers),
            reaction_steps=list(self.project.reaction_steps),
            generic_parameters=dict(self.project.generic_parameters),
            parameters=list(self.project.parameters),
            reaction_modifier_scripts=dict(self.project.reaction_modifier_scripts),
        )

    def _project_snapshot(self) -> dict:
        return self.project.to_dict()

    def _record_project_edit(self) -> None:
        self._undo_stack.append(self._project_snapshot())
        self._redo_stack.clear()
        self._update_undo_redo_actions()

    def _restore_project_snapshot(self, snapshot: dict) -> None:
        self.project = Project.from_dict(snapshot)
        self._sync_controls_from_project(self.project)
        self._populate_project_tree()
        self._populate_project_inspector()
        self._update_undo_redo_actions()

    def _undo_project_edit(self) -> None:
        if not self._undo_stack:
            return
        self._redo_stack.append(self._project_snapshot())
        self._restore_project_snapshot(self._undo_stack.pop())
        self._append_log("Undo project edit")

    def _redo_project_edit(self) -> None:
        if not self._redo_stack:
            return
        self._undo_stack.append(self._project_snapshot())
        self._restore_project_snapshot(self._redo_stack.pop())
        self._append_log("Redo project edit")

    def _update_undo_redo_actions(self) -> None:
        if hasattr(self, "undo_action"):
            self.undo_action.setEnabled(bool(self._undo_stack))
        if hasattr(self, "redo_action"):
            self.redo_action.setEnabled(bool(self._redo_stack))

    def _add_scripted_output(self) -> None:
        row = self.script_output_table.rowCount()
        self.script_output_table.insertRow(row)
        self.script_output_table.setItem(row, 0, QTableWidgetItem(f"scripted_{row + 1}"))
        self.script_output_table.setItem(row, 1, QTableWidgetItem("Mw / max(Mn, 1e-12)"))

    def _generate_script_template_row(self) -> None:
        species = tuple(item.get("name", "") for item in self.project.substances if item.get("name"))
        parameters = tuple(parameter.name for parameter in self.project.parameters)
        if not species:
            species = ("M",)
        if not parameters:
            parameters = ("kp",)
        row = self.script_output_table.rowCount()
        self.script_output_table.insertRow(row)
        self.script_output_table.setItem(row, 0, QTableWidgetItem(f"template_{row + 1}"))
        self.script_output_table.setItem(
            row,
            1,
            QTableWidgetItem(generate_script_template(species=species[:2], parameters=parameters[:2])),
        )

    def _populate_script_function_catalog(self) -> None:
        if not hasattr(self, "script_function_table"):
            return
        catalog = script_function_catalog()
        self.script_function_table.setRowCount(len(catalog))
        for row, spec in enumerate(catalog):
            values = [
                spec.name,
                ", ".join(spec.arguments),
                spec.category,
                "implemented" if spec.implemented else "stub",
                spec.description,
            ]
            for column, value in enumerate(values):
                self.script_function_table.setItem(row, column, QTableWidgetItem(value))

    def _add_debug_script_row(self) -> None:
        row = self.debug_script_table.rowCount()
        self.debug_script_table.insertRow(row)
        self.debug_script_table.setItem(row, 0, QTableWidgetItem(f"debug_{row + 1}"))
        self.debug_script_table.setItem(row, 1, QTableWidgetItem('x = getkp("GP_kp")\nresult = x * 2'))

    def _remove_selected_debug_script_row(self) -> None:
        row = self.debug_script_table.currentRow()
        if row >= 0:
            self.debug_script_table.removeRow(row)

    def _run_debug_scripts(self) -> None:
        rows: list[tuple[str, int, str, str, object]] = []
        state = ScriptCommandState(
            parameters=dict(self.project.generic_parameters),
            moments=self._current_debug_moments(),
            variables={"time": float(self.current_result.time[-1]) if self.current_result is not None else 0.0},
        )
        for row in range(self.debug_script_table.rowCount()):
            name = self._table_text(self.debug_script_table, row, 0).strip() or f"debug_{row + 1}"
            script = self._table_text(self.debug_script_table, row, 1)
            rows.extend(self._debug_script_trace(name, script, state))
        self.debug_trace_table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                self.debug_trace_table.setItem(row, column, QTableWidgetItem(str(value)))
        self._append_log(f"Debug scripts traced: {len(rows)} rows")

    def _move_debug_trace_to_window(self) -> None:
        table = QTableWidget(self.debug_trace_table.rowCount(), self.debug_trace_table.columnCount())
        headers = [
            self.debug_trace_table.horizontalHeaderItem(column).text()
            for column in range(self.debug_trace_table.columnCount())
        ]
        table.setHorizontalHeaderLabels(headers)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        for row in range(self.debug_trace_table.rowCount()):
            for column in range(self.debug_trace_table.columnCount()):
                source = self.debug_trace_table.item(row, column)
                table.setItem(row, column, QTableWidgetItem("" if source is None else source.text()))
        dock = QDockWidget("Debug trace", self)
        dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea)
        dock.setWidget(table)
        self.addDockWidget(Qt.RightDockWidgetArea, dock)
        self.debug_trace_dock = dock
        self.debug_trace_window_table = table
        self._append_log("Moved debug trace to dock window")

    def _debug_script_trace(
        self,
        name: str,
        script: str,
        state: ScriptCommandState,
    ) -> list[tuple[str, int, str, str, object]]:
        namespace = script_command_namespace(state)
        lines = script.splitlines()
        trace: list[tuple[str, int, str, str, object]] = []
        prefix: list[str] = []
        for line_number, line in enumerate(lines, start=1):
            text = line.strip()
            if not text:
                continue
            prefix.append(line)
            assignment = self._assignment_name(text)
            try:
                scope = evaluate_script_scope("\n".join(prefix), namespace)
                value = scope.get(assignment, "") if assignment else ""
            except Exception as exc:
                value = f"ERROR: {exc}"
            trace.append((name, line_number, text, assignment, value))
        return trace

    @staticmethod
    def _assignment_name(text: str) -> str:
        if "=" not in text or "==" in text:
            return ""
        lhs = text.split("=", 1)[0].strip()
        return lhs if lhs.isidentifier() else ""

    def _current_debug_moments(self) -> dict[str, float]:
        if self.current_result is None:
            return {}
        report = self.current_result.final_moments
        return {
            "M0": report.m0,
            "M1": report.m1,
            "M2": report.m2,
            "M3": report.m3,
            "Mn": report.mn,
            "Mw": report.mw,
            "PDI": report.pdi,
            "mass": report.mass,
        }

    def _apply_scripted_outputs_from_table(self) -> None:
        from predici_clone.api.project_schema import OutputConfig

        scripted = {}
        enabled = list(self.project.outputs.enabled_generic_outputs)
        for row in range(self.script_output_table.rowCount()):
            name_item = self.script_output_table.item(row, 0)
            expr_item = self.script_output_table.item(row, 1)
            if name_item is None or expr_item is None:
                continue
            name = name_item.text().strip()
            expression = expr_item.text().strip()
            if not name or not expression:
                continue
            scripted[name] = expression
            if name not in enabled:
                enabled.append(name)
        self._record_project_edit()
        self.project = Project(
            schema_version=self.project.schema_version,
            name=self.project.name,
            reactor=self.project.reactor,
            kinetics=self.project.kinetics,
            recipe=self.project.recipe,
            outputs=OutputConfig(
                distribution_mode=self.project.outputs.distribution_mode,
                log_axis=self.project.outputs.log_axis,
                gpc_convolution=self.project.outputs.gpc_convolution,
                enabled_generic_outputs=tuple(enabled),
                scripted_outputs=scripted,
                chart_pages=list(self.project.outputs.chart_pages),
                chart_graphs=list(self.project.outputs.chart_graphs),
            ),
            heat_balance=self.project.heat_balance,
            substances=list(self.project.substances),
            polymers=list(self.project.polymers),
            reaction_steps=list(self.project.reaction_steps),
            generic_parameters=dict(self.project.generic_parameters),
            parameters=list(self.project.parameters),
            reaction_modifier_scripts=dict(self.project.reaction_modifier_scripts),
        )
        self._populate_project_tree()
        self._append_log("Applied scripted outputs")

    def _refresh_recipe_table_from_controls(self) -> None:
        self._record_project_edit()
        self.project = self._project_from_controls()
        self._populate_recipe_table()
        self._populate_project_tree()

    def _populate_recipe_table(self) -> None:
        if not hasattr(self, "recipe_table"):
            return
        recipe = self.project.recipe
        rows = [
            ("recipe", "name", recipe.name),
            ("recipe", "unit_system", recipe.unit_system),
            ("initial", "monomer", recipe.initial.monomer),
            ("initial", "initiator", recipe.initial.initiator),
            ("feed", "monomer", recipe.feed.monomer),
            ("feed", "initiator", recipe.feed.initiator),
            ("feed", "rate", recipe.feed.rate),
            ("integration", "t_final", recipe.integration.t_final),
            ("integration", "output_points", recipe.integration.output_points),
            ("integration", "method", recipe.integration.method),
            ("integration", "backend", recipe.integration.backend),
            ("integration", "galerkin_cells", recipe.integration.galerkin_cells),
            ("integration", "galerkin_degree", recipe.integration.galerkin_degree),
            ("integration", "simulation_mode", recipe.integration.simulation_mode),
            ("integration", "include_monte_carlo", recipe.integration.include_monte_carlo),
            ("integration", "use_tau_leaping", recipe.integration.use_tau_leaping),
            ("reactor", "stages", self.project.reactor.stages),
            ("reactor", "axial_cells", self.project.reactor.axial_cells),
            ("profile", "temperature_points", len(recipe.temperature_profile)),
            ("profile", "pressure_points", len(recipe.pressure_profile)),
            ("profile", "pre_schedule_steps", len(recipe.pre_schedule)),
            ("feed_tanks", "count", len(recipe.feed_tanks)),
            ("polymer_feed", "count", len(recipe.polymer_feed)),
            ("heat", "enabled", self.project.heat_balance.enabled),
            ("heat", "heat_exchanger", self.project.heat_balance.use_heat_exchanger),
            ("heat", "coolant_temperature", self.project.heat_balance.coolant_temperature),
            ("heat", "additional_heat", self.project.heat_balance.additional_heat),
            ("shooting", "enabled", bool(recipe.shooting_control)),
        ]
        for index, point in enumerate(recipe.temperature_profile):
            rows.append((f"temperature_profile[{index}]", "time", point.time))
            rows.append((f"temperature_profile[{index}]", "value", point.value))
        for index, point in enumerate(recipe.pressure_profile):
            rows.append((f"pressure_profile[{index}]", "time", point.time))
            rows.append((f"pressure_profile[{index}]", "value", point.value))
        for index, step in enumerate(recipe.pre_schedule):
            rows.append((f"pre_schedule[{index}]", "time", step.get("time", 0.0)))
            rows.append((f"pre_schedule[{index}]", "action", step.get("action", "")))
            if "rate" in step:
                rows.append((f"pre_schedule[{index}]", "rate", step.get("rate", 0.0)))
            if "value" in step:
                rows.append((f"pre_schedule[{index}]", "value", step.get("value", 0.0)))
            if "temperature" in step:
                rows.append((f"pre_schedule[{index}]", "temperature", step.get("temperature", 0.0)))
            if "pressure" in step:
                rows.append((f"pre_schedule[{index}]", "pressure", step.get("pressure", 0.0)))
            if "residence_time" in step:
                rows.append((f"pre_schedule[{index}]", "residence_time", step.get("residence_time", 0.0)))
            if "coolant_temperature" in step:
                rows.append((f"pre_schedule[{index}]", "coolant_temperature", step.get("coolant_temperature", 0.0)))
            if "heat" in step:
                rows.append((f"pre_schedule[{index}]", "heat", step.get("heat", 0.0)))
            if "additional_heat" in step:
                rows.append((f"pre_schedule[{index}]", "additional_heat", step.get("additional_heat", 0.0)))
        for index, tank in enumerate(recipe.feed_tanks):
            rows.append((f"feed_tank[{index}]", "monomer", tank.monomer))
            rows.append((f"feed_tank[{index}]", "initiator", tank.initiator))
            rows.append((f"feed_tank[{index}]", "radicals", tank.radicals))
            rows.append((f"feed_tank[{index}]", "rate", tank.rate))
        for index, feed in enumerate(recipe.polymer_feed):
            rows.append((f"polymer_feed[{index}]", "name", feed.get("name", "polymer")))
            rows.append((f"polymer_feed[{index}]", "rate", feed.get("rate", 0.0)))
            rows.append((f"polymer_feed[{index}]", "mass_fraction", feed.get("mass_fraction", 1.0)))
            rows.append((f"polymer_feed[{index}]", "Mn", feed.get("Mn", 0.0)))
            rows.append((f"polymer_feed[{index}]", "Mw", feed.get("Mw", 0.0)))
        self.recipe_table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                self.recipe_table.setItem(row, column, QTableWidgetItem(str(value)))

    def _apply_recipe_table_edits(self) -> None:
        self._record_project_edit()
        values = self._recipe_table_values()
        recipe = self.project.recipe
        reactor = self.project.reactor
        heat = self.project.heat_balance
        updated_recipe = Recipe(
            name=str(values.get(("recipe", "name"), recipe.name)),
            unit_system=str(values.get(("recipe", "unit_system"), recipe.unit_system)),
            initial=InitialConditions(
                monomer=self._float_value(values, ("initial", "monomer"), recipe.initial.monomer),
                initiator=self._float_value(values, ("initial", "initiator"), recipe.initial.initiator),
                radicals=recipe.initial.radicals,
            ),
            feed=FeedStream(
                monomer=self._float_value(values, ("feed", "monomer"), recipe.feed.monomer),
                initiator=self._float_value(values, ("feed", "initiator"), recipe.feed.initiator),
                radicals=recipe.feed.radicals,
                rate=self._float_value(values, ("feed", "rate"), recipe.feed.rate),
            ),
            feed_tanks=self._feed_tanks_from_recipe_table(values, recipe.feed_tanks),
            polymer_feed=self._polymer_feed_from_recipe_table(values, recipe.polymer_feed),
            integration=IntegrationControl(
                t_final=self._float_value(values, ("integration", "t_final"), recipe.integration.t_final),
                output_points=self._int_value(values, ("integration", "output_points"), recipe.integration.output_points),
                method=str(values.get(("integration", "method"), recipe.integration.method)),
                rtol=recipe.integration.rtol,
                atol=recipe.integration.atol,
                backend=str(values.get(("integration", "backend"), recipe.integration.backend)),
                galerkin_cells=self._int_value(values, ("integration", "galerkin_cells"), recipe.integration.galerkin_cells),
                galerkin_degree=self._int_value(values, ("integration", "galerkin_degree"), recipe.integration.galerkin_degree),
                simulation_mode=str(values.get(("integration", "simulation_mode"), recipe.integration.simulation_mode)),
                include_monte_carlo=self._bool_value(
                    values,
                    ("integration", "include_monte_carlo"),
                    recipe.integration.include_monte_carlo,
                ),
                use_tau_leaping=self._bool_value(
                    values,
                    ("integration", "use_tau_leaping"),
                    recipe.integration.use_tau_leaping,
                ),
            ),
            pre_schedule=self._schedule_from_recipe_table(values, recipe.pre_schedule),
            temperature_profile=self._profile_from_recipe_table(values, "temperature_profile", recipe.temperature_profile),
            pressure_profile=self._profile_from_recipe_table(values, "pressure_profile", recipe.pressure_profile),
            shooting_control=dict(recipe.shooting_control),
        )
        updated_reactor = ReactorConfig(
            kind=reactor.kind,
            nmax=reactor.nmax,
            volume=reactor.volume,
            residence_time=reactor.residence_time,
            stages=self._int_value(values, ("reactor", "stages"), reactor.stages),
            axial_cells=self._int_value(values, ("reactor", "axial_cells"), reactor.axial_cells),
        )
        updated_heat = type(heat)(
            enabled=self._bool_value(values, ("heat", "enabled"), heat.enabled),
            use_heat_exchanger=self._bool_value(values, ("heat", "heat_exchanger"), heat.use_heat_exchanger),
            heat_transfer=heat.heat_transfer,
            area=heat.area,
            heat_capacity=heat.heat_capacity,
            mass_flow=heat.mass_flow,
            mass_holdup=heat.mass_holdup,
            initial_feed_temp=heat.initial_feed_temp,
            coolant_temperature=self._float_value(values, ("heat", "coolant_temperature"), heat.coolant_temperature),
            additional_heat=self._float_value(values, ("heat", "additional_heat"), heat.additional_heat),
            counter_current=heat.counter_current,
        )
        self.project = Project(
            schema_version=self.project.schema_version,
            name=self.project.name,
            reactor=updated_reactor,
            kinetics=self.project.kinetics,
            recipe=updated_recipe,
            outputs=self.project.outputs,
            heat_balance=updated_heat,
            substances=list(self.project.substances),
            polymers=list(self.project.polymers),
            reaction_steps=list(self.project.reaction_steps),
            generic_parameters=dict(self.project.generic_parameters),
            parameters=list(self.project.parameters),
            reaction_modifier_scripts=dict(self.project.reaction_modifier_scripts),
        )
        self._sync_controls_from_project(self.project)
        self._populate_project_tree()
        self._populate_project_inspector()
        self._append_log("Applied recipe table edits")

    def _add_recipe_consistency_row(self) -> None:
        row = self.recipe_consistency_table.rowCount()
        self.recipe_consistency_table.insertRow(row)
        name = "rest" if row == 0 else f"component_{row + 1}"
        for column, value in enumerate((name, "100.0", "1000.0", "0.0", "0.0", "0.0", "0.0", "0.0")):
            self.recipe_consistency_table.setItem(row, column, QTableWidgetItem(value))
        self._refresh_recipe_consistency_targets()

    def _set_recipe_concentration_consistent(self) -> None:
        try:
            target = self.recipe_consistency_target.currentText()
            adjusted = make_concentration_consistent(self._recipe_consistency_components(), target)
            self._set_recipe_consistency_components(adjusted)
            self._append_log("Set concentration consistent")
        except Exception as exc:
            QMessageBox.critical(self, "Consistency failed", str(exc))

    def _set_recipe_rest(self) -> None:
        try:
            target = self.recipe_consistency_target.currentText()
            adjusted = fill_remainder(self._recipe_consistency_components(), target, field="mass_part")
            self._set_recipe_consistency_components(adjusted)
            self._append_log("Set rest")
        except Exception as exc:
            QMessageBox.critical(self, "Set rest failed", str(exc))

    def _normalize_recipe_consistency_mode(self) -> None:
        try:
            mode = self.recipe_input_mode.currentText()
            composition = normalize_recipe_components(
                mode,
                self._recipe_consistency_components(),
                volume=self.recipe_basis_volume.value(),
                total_mass=self.recipe_basis_total_mass.value(),
                total_moles=self.recipe_basis_total_moles.value(),
            )
            self._set_recipe_consistency_components(composition.components)
            self.recipe_consistency_sum.setText(
                f"sum: {composition.consistency_sum:.6g} | volume: {composition.volume:.6g}"
            )
            self._append_log(f"Normalized recipe mode: {mode}")
        except Exception as exc:
            QMessageBox.critical(self, "Normalize recipe failed", str(exc))

    def _recipe_consistency_components(self) -> tuple[RecipeComponent, ...]:
        components: list[RecipeComponent] = []
        for row in range(self.recipe_consistency_table.rowCount()):
            name = self._table_text(self.recipe_consistency_table, row, 0).strip()
            if not name:
                continue
            components.append(
                RecipeComponent(
                    name=name,
                    molecular_weight=self._table_float(self.recipe_consistency_table, row, 1, 0.0),
                    density=self._table_float(self.recipe_consistency_table, row, 2, 0.0),
                    mass=self._table_float(self.recipe_consistency_table, row, 3, 0.0),
                    moles=self._table_float(self.recipe_consistency_table, row, 4, 0.0),
                    concentration=self._table_float(self.recipe_consistency_table, row, 5, 0.0),
                    mass_part=self._table_float(self.recipe_consistency_table, row, 6, 0.0),
                    mole_part=self._table_float(self.recipe_consistency_table, row, 7, 0.0),
                )
            )
        return tuple(components)

    def _set_recipe_consistency_components(self, components: tuple[RecipeComponent, ...]) -> None:
        self.recipe_consistency_table.setRowCount(len(components))
        for row, component in enumerate(components):
            values = [
                component.name,
                component.molecular_weight,
                component.density,
                component.mass,
                component.moles,
                component.concentration,
                component.mass_part,
                component.mole_part,
            ]
            for column, value in enumerate(values):
                self.recipe_consistency_table.setItem(row, column, QTableWidgetItem(f"{value:.12g}" if isinstance(value, float) else str(value)))
        self._refresh_recipe_consistency_targets()
        self._update_recipe_consistency_warning(components)

    def _update_recipe_consistency_warning(self, components: tuple[RecipeComponent, ...]) -> None:
        total = consistency_sum(components)
        inconsistent = bool(components) and abs(total - 1.0) > 1e-6
        suffix = " | inconsistent" if inconsistent else ""
        self.recipe_consistency_sum.setText(f"sum: {total:.6g}{suffix}")
        self.recipe_consistency_sum.setStyleSheet("color: #b91c1c; font-weight: 600;" if inconsistent else "")
        color = QColor("#fee2e2") if inconsistent else QColor("white")
        for row in range(self.recipe_consistency_table.rowCount()):
            for column in range(self.recipe_consistency_table.columnCount()):
                item = self.recipe_consistency_table.item(row, column)
                if item is not None:
                    item.setBackground(color)

    def _refresh_recipe_consistency_targets(self) -> None:
        current = self.recipe_consistency_target.currentText()
        names = [
            self._table_text(self.recipe_consistency_table, row, 0).strip()
            for row in range(self.recipe_consistency_table.rowCount())
            if self._table_text(self.recipe_consistency_table, row, 0).strip()
        ]
        self.recipe_consistency_target.clear()
        self.recipe_consistency_target.addItems(names or ["rest"])
        if current in names:
            self.recipe_consistency_target.setCurrentText(current)

    def _recipe_table_values(self) -> dict[tuple[str, str], str]:
        values: dict[tuple[str, str], str] = {}
        for row in range(self.recipe_table.rowCount()):
            section = self._table_text(self.recipe_table, row, 0).strip()
            field = self._table_text(self.recipe_table, row, 1).strip()
            value = self._table_text(self.recipe_table, row, 2).strip()
            if section and field:
                values[(section, field)] = value
        return values

    def _profile_from_recipe_table(self, values: dict[tuple[str, str], str], section_prefix: str, default: list[ProfilePoint]) -> list[ProfilePoint]:
        indexes = self._indexed_sections(values, section_prefix)
        if not indexes:
            return list(default)
        points = []
        for index in indexes:
            section = f"{section_prefix}[{index}]"
            if (section, "time") not in values or (section, "value") not in values:
                continue
            points.append(ProfilePoint(time=float(values[(section, "time")]), value=float(values[(section, "value")])))
        return sorted(points, key=lambda point: point.time)

    def _schedule_from_recipe_table(self, values: dict[tuple[str, str], str], default: list[dict]) -> list[dict]:
        indexes = self._indexed_sections(values, "pre_schedule")
        if not indexes:
            return list(default)
        steps = []
        for index in indexes:
            section = f"pre_schedule[{index}]"
            if (section, "time") not in values:
                continue
            action = values.get((section, "action"), "set_feed_rate")
            step = {"time": float(values[(section, "time")]), "action": action}
            if (section, "rate") in values:
                step["rate"] = float(values[(section, "rate")])
            if (section, "value") in values:
                step["value"] = float(values[(section, "value")])
            if (section, "temperature") in values:
                step["temperature"] = float(values[(section, "temperature")])
            if (section, "pressure") in values:
                step["pressure"] = float(values[(section, "pressure")])
            if (section, "residence_time") in values:
                step["residence_time"] = float(values[(section, "residence_time")])
            if (section, "coolant_temperature") in values:
                step["coolant_temperature"] = float(values[(section, "coolant_temperature")])
            if (section, "heat") in values:
                step["heat"] = float(values[(section, "heat")])
            if (section, "additional_heat") in values:
                step["additional_heat"] = float(values[(section, "additional_heat")])
            steps.append(step)
        return sorted(steps, key=lambda step: float(step.get("time", 0.0)))

    def _add_schedule_action_from_widgets(self) -> None:
        action = self.schedule_action_selector.currentText()
        value = self.schedule_value.value()
        payload = self._schedule_payload(action, value)
        self._record_project_edit()
        self.project = append_pre_schedule_step(self.project, self.schedule_time.value(), action, **payload)
        self._populate_recipe_table()
        self._populate_project_tree()
        self._populate_project_inspector()
        self._append_log(f"Added schedule action: {action}")

    @staticmethod
    def _schedule_payload(action: str, value: float) -> dict[str, float]:
        if action == "set_feed_rate":
            return {"rate": value}
        if action == "set_pressure":
            return {"pressure": value}
        if action == "set_additional_heat":
            return {"heat": value}
        if action == "set_residence_time":
            return {"value": value}
        if action == "set_coolant_temperature":
            return {"value": value}
        return {"value": value}

    def _feed_tanks_from_recipe_table(self, values: dict[tuple[str, str], str], default: list[FeedStream]) -> list[FeedStream]:
        indexes = self._indexed_sections(values, "feed_tank")
        if not indexes:
            return list(default)
        tanks = []
        for index in indexes:
            section = f"feed_tank[{index}]"
            tanks.append(
                FeedStream(
                    monomer=float(values.get((section, "monomer"), 0.0)),
                    initiator=float(values.get((section, "initiator"), 0.0)),
                    radicals=float(values.get((section, "radicals"), 0.0)),
                    rate=float(values.get((section, "rate"), 0.0)),
                )
            )
        return tanks

    def _polymer_feed_from_recipe_table(self, values: dict[tuple[str, str], str], default: list[dict]) -> list[dict]:
        indexes = self._indexed_sections(values, "polymer_feed")
        if not indexes:
            return list(default)
        feeds = []
        for index in indexes:
            section = f"polymer_feed[{index}]"
            feeds.append(
                {
                    "name": values.get((section, "name"), f"polymer_{index + 1}"),
                    "rate": float(values.get((section, "rate"), 0.0)),
                    "mass_fraction": float(values.get((section, "mass_fraction"), 1.0)),
                    "Mn": float(values.get((section, "Mn"), 0.0)),
                    "Mw": float(values.get((section, "Mw"), 0.0)),
                }
            )
        return feeds

    @staticmethod
    def _indexed_sections(values: dict[tuple[str, str], str], prefix: str) -> list[int]:
        indexes = set()
        marker = f"{prefix}["
        for section, _field in values:
            if section.startswith(marker) and section.endswith("]"):
                indexes.add(int(section[len(marker) : -1]))
        return sorted(indexes)

    @staticmethod
    def _float_value(values: dict[tuple[str, str], str], key: tuple[str, str], default: float) -> float:
        return float(values.get(key, default))

    @staticmethod
    def _int_value(values: dict[tuple[str, str], str], key: tuple[str, str], default: int) -> int:
        return int(float(values.get(key, default)))

    @staticmethod
    def _bool_value(values: dict[tuple[str, str], str], key: tuple[str, str], default: bool) -> bool:
        raw = str(values.get(key, default)).strip().lower()
        return raw in {"1", "true", "yes", "on"}

    def _run_simulation(self) -> None:
        try:
            self.project = self._project_from_controls()
            self._log_validation_messages(self.project)
            self._populate_project_tree()
            result = SimulationEngine(self.project).run()
            if not result.success:
                raise RuntimeError(result.message)
            self._set_result(result)
        except Exception as exc:
            QMessageBox.critical(self, "Simulation failed", str(exc))

    def _run_to_time_from_controls(self) -> None:
        try:
            self.project = self._project_from_controls()
            self._log_validation_messages(self.project)
            self._populate_project_tree()
            result = SimulationEngine(self.project).run_to_time(self.run_to_time_input.value())
            if not result.success:
                raise RuntimeError(result.message)
            self._set_result(result)
            self._append_log(f"Ran to t={result.time[-1]:.6g}")
        except Exception as exc:
            QMessageBox.critical(self, "Run-to-time failed", str(exc))

    def _single_step_from_controls(self) -> None:
        try:
            self.project = self._project_from_controls()
            self._log_validation_messages(self.project)
            self._populate_project_tree()
            engine = SimulationEngine(self.project)
            if self.current_result is not None:
                engine.run_to_time(float(self.current_result.time[-1]))
            result = engine.single_step()
            if not result.success:
                raise RuntimeError(result.message)
            self._set_result(result)
            self._append_log(f"Single step to t={result.time[-1]:.6g}")
        except Exception as exc:
            QMessageBox.critical(self, "Single step failed", str(exc))

    def _start_simulation_worker(self) -> None:
        if self._thread is not None:
            return
        self.progress.setValue(0)
        self.live_table.setRowCount(0)
        self.actual_values_table.setRowCount(0)
        self._thread = QThread(self)
        self.project = self._project_from_controls()
        self._populate_project_tree()
        self._worker = SimulationWorker(self.project)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(lambda value: self.progress.setValue(int(value * 100)))
        self._worker.step_done.connect(self._append_live_step)
        self._worker.log.connect(self._append_log)
        self._worker.error.connect(self._worker_error)
        self._worker.finished.connect(self._worker_finished)
        self._worker.finished.connect(self._thread.quit)
        self._worker.error.connect(self._thread.quit)
        self._thread.finished.connect(self._cleanup_worker)
        self._thread.start()
        self.statusBar().showMessage("Simulation running")

    def _request_stop(self) -> None:
        if self._worker is not None:
            self._worker.request_stop()
            self._append_log("Stop requested")

    def _worker_finished(self, result: SimulationResult) -> None:
        self._set_result(result)
        self.statusBar().showMessage("Simulation finished")

    def _worker_error(self, message: str) -> None:
        self._append_log(f"ERROR: {message}")
        QMessageBox.critical(self, "Simulation failed", message)

    def _cleanup_worker(self) -> None:
        if self._worker is not None:
            self._worker.deleteLater()
        if self._thread is not None:
            self._thread.deleteLater()
        self._worker = None
        self._thread = None

    def _append_live_step(self, snapshot: object) -> None:
        data = dict(snapshot)
        row = self.live_table.rowCount()
        self.live_table.insertRow(row)
        for column, key in enumerate(["time", "Mn", "Mw", "PDI"]):
            self.live_table.setItem(row, column, QTableWidgetItem(f"{data[key]:.6g}"))

    def _append_log(self, message: str) -> None:
        self.log.appendPlainText(message)

    def _set_result(self, result: SimulationResult) -> None:
        if self.current_result is not None:
            self._remember_mwd_overlay(
                f"{self.current_result.reactor_kind} previous",
                self.current_result.final_distribution,
                self.current_result.first_length,
            )
        self.current_result = result
        self._populate_project_tree()
        self._configure_mwd_time_slider(result)
        self._set_distribution(result.final_distribution, first_length=result.first_length, title=result.reactor_kind)
        moments = result.final_moments
        self.dashboard_summary.setText(
            f"{result.reactor_kind} | Mn={moments.mn:.4g} | Mw={moments.mw:.4g} | PDI={moments.pdi:.4g}"
        )
        self._fill_table(self.output_table, generic_outputs_frame(result, self.project.outputs))
        self._sync_fitting_target_from_result(result)
        self._populate_inspector(
            {
                "reactor": result.reactor_kind,
                "time points": len(result.time),
                "distribution bins": result.final_distribution.size,
                "solver": result.metadata.get("solver_status"),
            }
        )
        self._populate_actual_values_table(result)
        self.progress.setValue(100)

    def _populate_actual_values_table(self, result: SimulationResult) -> None:
        rows = result.actual_values_history()
        self.actual_values_table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, key in enumerate(("step_index", "time", "stepsize", "n_variables")):
                value = values[key]
                text = str(int(value)) if key in {"step_index", "n_variables"} else f"{value:.6g}"
                self.actual_values_table.setItem(row, column, QTableWidgetItem(text))

    def _sync_fitting_target_from_result(self, result: SimulationResult) -> None:
        if not hasattr(self, "fitting_target_table"):
            return
        self.fitting_target_table.setItem(0, 1, QTableWidgetItem(f"{result.final_moments.mass:.12g}"))

    def _fit_gpkp_to_current_mass(self) -> None:
        self._run_fitting(global_search=False)

    def _global_search_gpkp_to_current_mass(self) -> None:
        self._run_fitting(global_search=True)

    def _bayesian_sample_gpkp_to_current_mass(self) -> None:
        if self.current_result is None:
            return
        try:
            problem = self._fitting_problem_from_tables()
            result = sample_bayesian_posterior(problem, samples=32, burn_in=8, step_scale=0.08, seed=3)
            rows = [
                ("samples", result.samples.shape[0]),
                ("acceptance_rate", result.acceptance_rate),
                ("log_posterior_final", result.log_posterior[-1] if result.log_posterior.size else ""),
            ]
            for name in result.parameter_names:
                rows.append((f"{name}_mean", result.posterior_mean[name]))
                lo, hi = result.credible_intervals[name]
                rows.append((f"{name}_ci95_low", lo))
                rows.append((f"{name}_ci95_high", hi))
            self._fill_fitting_result_table(rows)
            self._append_log("Bayesian sampling completed")
        except Exception as exc:
            QMessageBox.critical(self, "Bayesian sampling failed", str(exc))

    def _multi_experiment_fit_gpkp(self) -> None:
        if self.current_result is None:
            return
        try:
            problem = self._multi_experiment_problem_from_table()
            result = fit_multi_experiment_generic_parameters(problem)
            rows = [
                ("success", result.success),
                ("message", result.message),
                ("residual_norm", result.residual_norm),
                ("evaluations", result.evaluations),
                ("experiments", len(problem.experiments)),
                *result.parameters.items(),
            ]
            if result.condition_number is not None:
                rows.append(("condition_number", result.condition_number))
            self._fill_fitting_result_table(rows)
            self._append_log("Multi-experiment fitting completed")
        except Exception as exc:
            QMessageBox.critical(self, "Multi-experiment fitting failed", str(exc))

    def _multi_experiment_bayesian_sample(self) -> None:
        if self.current_result is None:
            return
        try:
            problem = self._multi_experiment_problem_from_table()
            result = sample_multi_experiment_bayesian_posterior(problem, samples=32, burn_in=8, step_scale=0.08, seed=5)
            rows = [
                ("samples", result.samples.shape[0]),
                ("acceptance_rate", result.acceptance_rate),
                ("experiments", len(problem.experiments)),
                ("log_posterior_final", result.log_posterior[-1] if result.log_posterior.size else ""),
            ]
            for name in result.parameter_names:
                rows.append((f"{name}_mean", result.posterior_mean[name]))
                lo, hi = result.credible_intervals[name]
                rows.append((f"{name}_ci95_low", lo))
                rows.append((f"{name}_ci95_high", hi))
            self._fill_fitting_result_table(rows)
            self._append_log("Multi-experiment Bayesian sampling completed")
        except Exception as exc:
            QMessageBox.critical(self, "Multi-experiment Bayesian sampling failed", str(exc))

    def _multi_experiment_problem_from_table(self) -> MultiExperimentFittingProblem:
        specs = self._parameter_specs_from_table()
        experiments = []
        for row in range(self.fitting_experiment_table.rowCount()):
            name = self._table_text(self.fitting_experiment_table, row, 0).strip() or f"experiment_{row + 1}"
            t_final = float(self._table_text(self.fitting_experiment_table, row, 1))
            output = self._table_text(self.fitting_experiment_table, row, 2).strip() or "mass"
            target = float(self._table_text(self.fitting_experiment_table, row, 3))
            weight = float(self._table_text(self.fitting_experiment_table, row, 4))
            experiments.append(
                FittingExperiment(
                    name=name,
                    project=self._project_with_t_final(t_final, required_outputs=(output,)),
                    targets=(OutputTarget(output, target, weight),),
                )
            )
        return MultiExperimentFittingProblem(experiments=tuple(experiments), parameters=specs)

    def _load_residual_csv_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load experiment data", str(Path.cwd()), "CSV (*.csv)")
        if path:
            self._load_residual_csv(Path(path))

    def _load_residual_csv(self, path: Path, *, start: float | None = None, end: float | None = None) -> None:
        dataset = load_experiment_csv(path)
        self.fitting_raw_residual_dataset = dataset
        if start is not None or end is not None:
            dataset = trim_experiment(dataset, start=start, end=end)
        self.fitting_residual_dataset = dataset
        self._append_log(f"Loaded residual data: {path}")
        self._evaluate_loaded_residuals()

    def _evaluate_loaded_residuals(self) -> None:
        dataset = getattr(self, "fitting_raw_residual_dataset", None) or getattr(self, "fitting_residual_dataset", None)
        if dataset is None:
            return
        try:
            mappings = self._residual_mappings_from_table(dataset)
            start, end = self._residual_trim_window_from_table()
            if start is not None or end is not None:
                dataset = trim_experiment(dataset, start=start, end=end)
            self.fitting_residual_dataset = dataset
            frame = residual_frame(
                self._project_with_t_final(self.project.recipe.integration.t_final, required_outputs=tuple(mapping.output for mapping in mappings)),
                dataset,
                mappings,
            )
            self._fill_table(self.fitting_residual_table, frame)
            self._plot_residual_frame(frame)
            self._append_log("Residuals evaluated")
        except Exception as exc:
            QMessageBox.critical(self, "Residual evaluation failed", str(exc))

    def _plot_residual_frame(self, frame) -> None:
        self.fitting_residual_figure.clear()
        axes = self.fitting_residual_figure.add_subplot(111)
        if not frame.empty:
            axes.scatter(frame["time"], frame["residual"], color="#9c2f2f", s=18)
            axes.axhline(0.0, color="#555555", linewidth=1)
        axes.set_xlabel("time")
        axes.set_ylabel("weighted residual")
        axes.grid(True, alpha=0.25)
        self.fitting_residual_canvas.draw_idle()

    def _residual_mappings_from_table(self, dataset: ExperimentDataset) -> tuple[DataMapping, ...]:
        mappings = []
        for row in range(self.fitting_residual_mapping_table.rowCount()):
            output = self._table_text(self.fitting_residual_mapping_table, row, 0).strip()
            if not output:
                continue
            column = self._table_text(self.fitting_residual_mapping_table, row, 1).strip()
            if not column:
                column = f"{output}_obs" if f"{output}_obs" in dataset.frame.columns else output
            if column not in dataset.frame.columns:
                raise ValueError(f"Missing observation column: {column}")
            weight_text = self._table_text(self.fitting_residual_mapping_table, row, 2).strip() or "1.0"
            mappings.append(DataMapping(output, column, float(weight_text)))
        if not mappings:
            output = self._table_text(self.fitting_target_table, 0, 0).strip() or "mass"
            column = f"{output}_obs" if f"{output}_obs" in dataset.frame.columns else output
            if column not in dataset.frame.columns:
                raise ValueError(f"Missing observation column: {column}")
            mappings.append(DataMapping(output, column, 1.0))
        return tuple(mappings)

    def _residual_trim_window_from_table(self) -> tuple[float | None, float | None]:
        starts = []
        ends = []
        for row in range(self.fitting_residual_mapping_table.rowCount()):
            start = self._table_text(self.fitting_residual_mapping_table, row, 3).strip()
            end = self._table_text(self.fitting_residual_mapping_table, row, 4).strip()
            if start:
                starts.append(float(start))
            if end:
                ends.append(float(end))
        return (max(starts) if starts else None, min(ends) if ends else None)

    def _add_residual_mapping_row(self) -> None:
        row = self.fitting_residual_mapping_table.rowCount()
        self.fitting_residual_mapping_table.insertRow(row)
        defaults = ["Mn", "Mn_obs", "1.0", "", ""]
        for column, value in enumerate(defaults):
            self.fitting_residual_mapping_table.setItem(row, column, QTableWidgetItem(value))

    def _remove_selected_residual_mapping_row(self) -> None:
        row = self.fitting_residual_mapping_table.currentRow()
        if row >= 0 and self.fitting_residual_mapping_table.rowCount() > 1:
            self.fitting_residual_mapping_table.removeRow(row)

    def _run_fitting(self, *, global_search: bool) -> None:
        if self.current_result is None:
            return
        try:
            problem = self._fitting_problem_from_tables()
            result = global_search_generic_parameters(problem, maxiter=4) if global_search else fit_generic_parameters(problem)
            rows = [
                ("success", result.success),
                ("message", result.message),
                ("residual_norm", result.residual_norm),
                ("evaluations", result.evaluations),
                *result.parameters.items(),
            ]
            self._fill_fitting_result_table(rows)
            self._append_log("Fitting completed")
        except Exception as exc:
            QMessageBox.critical(self, "Fitting failed", str(exc))

    def _fitting_problem_from_tables(self) -> FittingProblem:
        specs = self._parameter_specs_from_table()
        target = OutputTarget(
            name=self.fitting_target_table.item(0, 0).text(),
            value=float(self.fitting_target_table.item(0, 1).text()),
            weight=float(self.fitting_target_table.item(0, 2).text()),
        )
        return FittingProblem(
            project=self._project_with_t_final(self.project.recipe.integration.t_final, required_outputs=(target.name,)),
            parameters=specs,
            targets=(target,),
        )

    def _parameter_spec_from_table(self) -> ParameterSpec:
        return self._parameter_specs_from_table()[0]

    def _parameter_specs_from_table(self) -> tuple[ParameterSpec, ...]:
        specs = []
        for row in range(self.fitting_parameter_table.rowCount()):
            name = self._table_text(self.fitting_parameter_table, row, 0).strip()
            if not name:
                continue
            specs.append(
                ParameterSpec(
                    name=name,
                    initial=float(self._table_text(self.fitting_parameter_table, row, 1)),
                    lower=float(self._table_text(self.fitting_parameter_table, row, 2)),
                    upper=float(self._table_text(self.fitting_parameter_table, row, 3)),
                    fixed=self._table_text(self.fitting_parameter_table, row, 4).lower() == "true",
                )
            )
        if not specs:
            raise ValueError("At least one fitting parameter is required")
        return tuple(specs)

    def _add_fitting_parameter_row(self) -> None:
        row = self.fitting_parameter_table.rowCount()
        self.fitting_parameter_table.insertRow(row)
        defaults = [f"GP_param_{row + 1}", "0.01", "0.0", "1.0", "True"]
        for column, value in enumerate(defaults):
            self.fitting_parameter_table.setItem(row, column, QTableWidgetItem(value))

    def _remove_selected_fitting_parameter_row(self) -> None:
        row = self.fitting_parameter_table.currentRow()
        if row >= 0 and self.fitting_parameter_table.rowCount() > 1:
            self.fitting_parameter_table.removeRow(row)

    def _project_with_t_final(self, t_final: float, *, required_outputs: tuple[str, ...] = ()) -> Project:
        recipe = Recipe(
            name=self.project.recipe.name,
            unit_system=self.project.recipe.unit_system,
            initial=self.project.recipe.initial,
            feed=self.project.recipe.feed,
            feed_tanks=list(self.project.recipe.feed_tanks),
            polymer_feed=list(self.project.recipe.polymer_feed),
            integration=IntegrationControl(
                t_final=t_final,
                output_points=self.project.recipe.integration.output_points,
                method=self.project.recipe.integration.method,
                rtol=self.project.recipe.integration.rtol,
                atol=self.project.recipe.integration.atol,
                backend=self.project.recipe.integration.backend,
                galerkin_cells=self.project.recipe.integration.galerkin_cells,
                galerkin_degree=self.project.recipe.integration.galerkin_degree,
                simulation_mode=self.project.recipe.integration.simulation_mode,
                include_monte_carlo=self.project.recipe.integration.include_monte_carlo,
                use_tau_leaping=self.project.recipe.integration.use_tau_leaping,
            ),
            pre_schedule=list(self.project.recipe.pre_schedule),
            temperature_profile=list(self.project.recipe.temperature_profile),
            pressure_profile=list(self.project.recipe.pressure_profile),
            shooting_control=dict(self.project.recipe.shooting_control),
        )
        enabled_outputs = list(self.project.outputs.enabled_generic_outputs)
        for output in required_outputs:
            if output not in enabled_outputs:
                enabled_outputs.append(output)
        outputs = OutputConfig(
            distribution_mode=self.project.outputs.distribution_mode,
            log_axis=self.project.outputs.log_axis,
            gpc_convolution=self.project.outputs.gpc_convolution,
            enabled_generic_outputs=tuple(enabled_outputs),
            scripted_outputs=dict(self.project.outputs.scripted_outputs),
            chart_pages=list(self.project.outputs.chart_pages),
            chart_graphs=list(self.project.outputs.chart_graphs),
        )
        return Project(
            schema_version=self.project.schema_version,
            name=self.project.name,
            reactor=self.project.reactor,
            kinetics=self.project.kinetics,
            recipe=recipe,
            outputs=outputs,
            heat_balance=self.project.heat_balance,
            substances=list(self.project.substances),
            polymers=list(self.project.polymers),
            reaction_steps=list(self.project.reaction_steps),
            generic_parameters=dict(self.project.generic_parameters),
            parameters=list(self.project.parameters),
            reaction_modifier_scripts=dict(self.project.reaction_modifier_scripts),
        )

    def _fill_fitting_result_table(self, rows: list[tuple[str, object]]) -> None:
        self.fitting_result_table.setRowCount(len(rows))
        for row, (name, value) in enumerate(rows):
            self.fitting_result_table.setItem(row, 0, QTableWidgetItem(str(name)))
            self.fitting_result_table.setItem(row, 1, QTableWidgetItem(str(value)))

    def _load_benchmark(self) -> None:
        case = self.benchmark_cases[self.benchmark_combo.currentIndex()]
        frame = case.frame
        if self.current_distribution.size:
            self._remember_mwd_overlay(
                "current run",
                self.current_distribution,
                self.current_first_length,
            )
        self.mwd_time_slider.setEnabled(False)
        self.mwd_time_label.setText("time: reference")
        self._set_distribution(
            frame["concentration"].to_numpy(),
            first_length=int(frame["chain_length"].iloc[0]),
            title=case.name,
            explicit_lengths=frame["chain_length"].to_numpy(),
        )
        self.dashboard_summary.setText(f"{case.name}\n{case.source}\n{case.note}")
        self.summary_label.setText(f"{case.name}\n{case.source}\n{case.note}")
        self._populate_inspector({"benchmark": case.name, "source": case.source, "rows": len(frame)})

    def _configure_mwd_time_slider(self, result: SimulationResult) -> None:
        count = len(result.time)
        self.mwd_time_slider.blockSignals(True)
        self.mwd_time_slider.setMinimum(0)
        self.mwd_time_slider.setMaximum(max(count - 1, 0))
        self.mwd_time_slider.setValue(max(count - 1, 0))
        self.mwd_time_slider.setEnabled(count > 1)
        self.mwd_time_slider.blockSignals(False)
        self.current_time_index = max(count - 1, 0)
        self._update_mwd_time_label()

    def _show_mwd_time_index(self, index: int) -> None:
        if self.current_result is None:
            return
        self.current_time_index = int(index)
        distribution = self.current_result.distribution_history[:, self.current_time_index]
        title = f"{self.current_result.reactor_kind} @ t={self.current_result.time[self.current_time_index]:.4g}"
        self._set_distribution(distribution, first_length=self.current_result.first_length, title=title)
        self._update_mwd_time_label()

    def _update_mwd_time_label(self) -> None:
        if self.current_result is None or self.current_time_index < 0:
            return
        time = self.current_result.time[self.current_time_index]
        self.mwd_time_label.setText(f"time: {time:.6g}")

    def _remember_mwd_overlay(self, label: str, distribution: np.ndarray, first_length: int) -> None:
        values = np.asarray(distribution, dtype=float).copy()
        if values.size == 0:
            return
        self.mwd_overlays.append(
            {
                "label": label,
                "distribution": values,
                "first_length": int(first_length),
            }
        )
        self.mwd_overlays = self.mwd_overlays[-4:]

    def _clear_mwd_overlays(self) -> None:
        self.mwd_overlays.clear()
        self._redraw_current_distribution()
        self._append_log("Cleared MWD overlays")

    def _redraw_current_distribution(self) -> None:
        self._set_distribution(
            self.current_distribution,
            first_length=self.current_first_length,
            title="Molecular weight distribution",
            explicit_lengths=self.current_explicit_lengths,
        )

    def _mwd_monomer_mw(self) -> float:
        value = self.project.generic_parameters.get("monomer_mw", 100.0)
        try:
            return max(float(value), 1e-12)
        except (TypeError, ValueError):
            return 100.0

    def _mwd_gpc_sigma(self) -> float:
        value = self.project.generic_parameters.get("gpc_sigma", 1.5)
        try:
            return max(float(value), 0.0)
        except (TypeError, ValueError):
            return 1.5

    def _mwd_series(
        self,
        distribution: np.ndarray,
        *,
        first_length: int,
        explicit_lengths: np.ndarray | None = None,
    ) -> tuple[np.ndarray, np.ndarray, str, str]:
        values = np.maximum(np.asarray(distribution, dtype=float), 0.0)
        mode_text = self.mwd_mode_selector.currentText() if hasattr(self, "mwd_mode_selector") else "weight fraction"
        axis_text = self.mwd_axis_selector.currentText() if hasattr(self, "mwd_axis_selector") else "chain length"
        use_gpc = bool(hasattr(self, "mwd_gpc_toggle") and self.mwd_gpc_toggle.isChecked())
        mode = "number" if mode_text.startswith("mole") else "weight"

        if use_gpc and explicit_lengths is None:
            profile = distribution_to_gpc_profile(
                values,
                first_length=first_length,
                monomer_mw=self._mwd_monomer_mw(),
                mode=mode,
                log_axis=axis_text.startswith("log"),
                convolution_sigma=self._mwd_gpc_sigma(),
            )
            x = profile.x
            x_label = profile.x_label
            if axis_text == "chain length":
                x = np.arange(first_length, first_length + values.size, dtype=float)
                x_label = "chain length"
            y_label = "mole fraction" if mode == "number" else profile.y_label
            return x, profile.y, x_label, y_label

        lengths = (
            np.arange(first_length, first_length + values.size, dtype=float)
            if explicit_lengths is None
            else np.asarray(explicit_lengths, dtype=float)
        )
        molecular_weight = np.maximum(lengths * self._mwd_monomer_mw(), 1e-12)
        if mode == "number":
            y = values.copy()
            y_label = "mole fraction"
        else:
            y = values * molecular_weight
            y_label = "weight fraction"
        total = float(np.sum(y))
        if total > 0:
            y = y / total
        if axis_text.startswith("log"):
            return np.log10(molecular_weight), y, "log10 molecular weight", y_label
        if axis_text == "molecular weight":
            return molecular_weight, y, "molecular weight", y_label
        return lengths, y, "chain length", y_label

    def _set_distribution(
        self,
        distribution: np.ndarray,
        *,
        first_length: int,
        title: str,
        explicit_lengths: np.ndarray | None = None,
    ) -> None:
        self.current_distribution = np.asarray(distribution, dtype=float)
        self.current_first_length = first_length
        self.current_explicit_lengths = None if explicit_lengths is None else np.asarray(explicit_lengths, dtype=float)
        lengths = (
            np.arange(first_length, first_length + self.current_distribution.size)
            if explicit_lengths is None
            else np.asarray(explicit_lengths, dtype=float)
        )
        report = (
            from_discrete_distribution(self.current_distribution, first_length=first_length)
            if explicit_lengths is None
            else MomentReport(
                m0=float(np.sum(self.current_distribution)),
                m1=float(np.sum(lengths * self.current_distribution)),
                m2=float(np.sum(lengths * lengths * self.current_distribution)),
                m3=float(np.sum(lengths * lengths * lengths * self.current_distribution)),
            )
        )
        x, y, x_label, y_label = self._mwd_series(
            self.current_distribution,
            first_length=first_length,
            explicit_lengths=self.current_explicit_lengths,
        )
        self.figure.clear()
        axes = self.figure.add_subplot(111)
        axes.plot(x, y, color="#26547c", linewidth=2)
        if self.mwd_overlay_toggle.isChecked():
            for overlay in self.mwd_overlays:
                overlay_distribution = np.asarray(overlay["distribution"], dtype=float)
                overlay_first = int(overlay["first_length"])
                overlay_x, overlay_y, _, _ = self._mwd_series(
                    overlay_distribution,
                    first_length=overlay_first,
                )
                axes.plot(
                    overlay_x,
                    overlay_y,
                    linewidth=1.2,
                    alpha=0.65,
                    label=str(overlay["label"]),
                )
            if self.mwd_overlays:
                axes.legend(loc="best")
        axes.set_title(title)
        axes.set_xlabel(x_label)
        axes.set_ylabel(y_label)
        axes.grid(True, alpha=0.25)
        self.canvas.draw_idle()
        self._fill_table(self.moment_table, report_frame(report))
        self._populate_component_info_board(report, lengths)
        self.summary_label.setText(f"Mn={report.mn:.4g}  Mw={report.mw:.4g}  PDI={report.pdi:.4g}")

    def _populate_component_info_board(self, report: MomentReport, lengths: np.ndarray) -> None:
        if not hasattr(self, "component_info_table"):
            return
        values = np.maximum(np.asarray(self.current_distribution, dtype=float), 0.0)
        monomer_mw = self._mwd_monomer_mw()
        rows = [
            ("concentration_mol", float(np.sum(values))),
            ("concentration_mass", float(np.sum(values * lengths * monomer_mw))),
            ("mn", report.mn),
            ("mw", report.mw),
            ("dispersity", report.pdi),
            ("reference_volume", self.project.reactor.volume),
            ("last_value", float(values[-1]) if values.size else 0.0),
        ]
        self.component_info_table.setRowCount(len(rows))
        for row, (name, value) in enumerate(rows):
            self.component_info_table.setItem(row, 0, QTableWidgetItem(name))
            item = QTableWidgetItem(f"{value:.12g}")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.component_info_table.setItem(row, 1, item)

    def _populate_chart_administration(self) -> None:
        if not hasattr(self, "chart_page_table"):
            return
        pages = self.project.outputs.chart_pages or [{"page": "Standard", "title": "Standard", "layout": "2x2"}]
        graphs = self.project.outputs.chart_graphs or [
            {
                "page": "Standard",
                "graph": "MWD",
                "graphic_mode": "distribution",
                "distribution_y_axis": "weight",
                "x_axis_kind": "chain_length",
                "x_axis_scale": "linear",
                "source": "current",
            }
        ]
        self.chart_page_table.setRowCount(len(pages))
        for row, page in enumerate(pages):
            values = [
                page.get("page", "Standard"),
                page.get("title", page.get("page", "Standard")),
                page.get("layout", "2x2"),
            ]
            for column, value in enumerate(values):
                self.chart_page_table.setItem(row, column, QTableWidgetItem(str(value)))
        self.chart_graph_table.setRowCount(len(graphs))
        for row, graph in enumerate(graphs):
            values = [
                graph.get("page", "Standard"),
                graph.get("graph", f"Graph {row + 1}"),
                graph.get("graphic_mode", "distribution"),
                graph.get("distribution_y_axis", graph.get("moment_y_axis", "weight")),
                graph.get("x_axis_kind", "chain_length"),
                graph.get("x_axis_scale", "linear"),
                graph.get("source", "current"),
            ]
            for column, value in enumerate(values):
                self.chart_graph_table.setItem(row, column, QTableWidgetItem(str(value)))

    def _add_chart_page_row(self) -> None:
        row = self.chart_page_table.rowCount()
        self.chart_page_table.insertRow(row)
        for column, value in enumerate((f"Page {row + 1}", f"Page {row + 1}", "2x2")):
            self.chart_page_table.setItem(row, column, QTableWidgetItem(value))

    def _add_chart_graph_row(self) -> None:
        row = self.chart_graph_table.rowCount()
        page = self._table_text(self.chart_page_table, 0, 0).strip() or "Standard"
        self.chart_graph_table.insertRow(row)
        for column, value in enumerate((page, f"Graph {row + 1}", "distribution", "weight", "chain_length", "linear", "current")):
            self.chart_graph_table.setItem(row, column, QTableWidgetItem(value))

    def _apply_chart_administration(self) -> None:
        self._record_project_edit()
        pages = []
        for row in range(self.chart_page_table.rowCount()):
            page = self._table_text(self.chart_page_table, row, 0).strip()
            if not page:
                continue
            pages.append(
                {
                    "page": page,
                    "title": self._table_text(self.chart_page_table, row, 1).strip() or page,
                    "layout": self._table_text(self.chart_page_table, row, 2).strip() or "2x2",
                }
            )
        graphs = []
        for row in range(self.chart_graph_table.rowCount()):
            graph = self._table_text(self.chart_graph_table, row, 1).strip()
            if not graph:
                continue
            mode = self._table_text(self.chart_graph_table, row, 2).strip() or "distribution"
            y_axis = self._table_text(self.chart_graph_table, row, 3).strip() or "weight"
            entry = {
                "page": self._table_text(self.chart_graph_table, row, 0).strip() or "Standard",
                "graph": graph,
                "graphic_mode": mode,
                "x_axis_kind": self._table_text(self.chart_graph_table, row, 4).strip() or "chain_length",
                "x_axis_scale": self._table_text(self.chart_graph_table, row, 5).strip() or "linear",
                "source": self._table_text(self.chart_graph_table, row, 6).strip() or "current",
            }
            if mode == "moment":
                entry["moment_y_axis"] = y_axis
            else:
                entry["distribution_y_axis"] = y_axis
            graphs.append(entry)
        self.project = Project(
            schema_version=self.project.schema_version,
            name=self.project.name,
            reactor=self.project.reactor,
            kinetics=self.project.kinetics,
            recipe=self.project.recipe,
            outputs=OutputConfig(
                distribution_mode=self.project.outputs.distribution_mode,
                log_axis=self.project.outputs.log_axis,
                gpc_convolution=self.project.outputs.gpc_convolution,
                enabled_generic_outputs=self.project.outputs.enabled_generic_outputs,
                scripted_outputs=dict(self.project.outputs.scripted_outputs),
                chart_pages=pages,
                chart_graphs=graphs,
            ),
            heat_balance=self.project.heat_balance,
            substances=list(self.project.substances),
            polymers=list(self.project.polymers),
            reaction_steps=list(self.project.reaction_steps),
            general_kinetic_steps=list(self.project.general_kinetic_steps),
            general_initial_conditions=dict(self.project.general_initial_conditions),
            generic_parameters=dict(self.project.generic_parameters),
            parameters=list(self.project.parameters),
            reaction_modifier_scripts=dict(self.project.reaction_modifier_scripts),
        )
        self._populate_project_tree()
        self._populate_project_inspector()
        self._append_log("Applied chart administration")

    def _fill_table(self, table: QTableWidget, frame) -> None:
        table.setRowCount(len(frame))
        table.setColumnCount(len(frame.columns))
        table.setHorizontalHeaderLabels([str(column) for column in frame.columns])
        for row in range(len(frame)):
            for column, name in enumerate(frame.columns):
                item = QTableWidgetItem(str(frame.iloc[row][name]))
                if column > 0:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                table.setItem(row, column, item)
        table.resizeColumnsToContents()

    def _populate_inspector(self, values: dict[str, object]) -> None:
        self.inspector.setRowCount(len(values))
        for row, (name, value) in enumerate(values.items()):
            self.inspector.setItem(row, 0, QTableWidgetItem(str(name)))
            self.inspector.setItem(row, 1, QTableWidgetItem(str(value)))

    def _save_report(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export chart/data",
            str(Path.cwd() / "distribution.csv"),
            "CSV (*.csv);;Excel (*.xlsx);;PNG (*.png);;PDF (*.pdf)",
        )
        if not path:
            return
        suffix = Path(path).suffix.lower()
        if suffix in {".png", ".pdf"}:
            save_distribution_plot(path, self.current_distribution, first_length=self.current_first_length)
            self._append_log(f"Exported chart: {path}")
            return
        write_distribution_report(path, self.current_distribution, first_length=self.current_first_length)
        self._append_log(f"Exported report: {path}")

    def _open_sample_project(self) -> None:
        self._record_project_edit()
        self.project = sample_project(self.reactor_kind.currentText())
        self.current_project_path = None
        self._sync_controls_from_project(self.project)
        self._populate_project_tree()
        self._populate_project_inspector()
        self._update_undo_redo_actions()
        self._append_log("Opened sample project")
        self.statusBar().showMessage("Opened sample project")
        self._run_simulation()

    def _open_project_dialog(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open project", str(Path.cwd()), "PREDICI Project (*.predici.json *.json)")
        if path:
            self._open_project_from_path(Path(path))

    def _save_project_dialog(self) -> None:
        default = self.current_project_path or Path.cwd() / "project.predici.json"
        path, _ = QFileDialog.getSaveFileName(self, "Save project", str(default), "PREDICI Project (*.predici.json *.json)")
        if path:
            self._save_project_to_path(Path(path))

    def _save_result_dialog(self) -> None:
        default = Path.cwd() / "results" / "run_001"
        path = QFileDialog.getExistingDirectory(self, "Save result directory", str(default.parent))
        if path:
            self._save_result_to_directory(Path(path))

    def _open_project_from_path(self, path: Path) -> None:
        self.project = load_project(path)
        self.current_project_path = path
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._sync_controls_from_project(self.project)
        self._populate_project_tree()
        self._populate_project_inspector()
        self._update_undo_redo_actions()
        self._append_log(f"Opened project: {path}")
        self.statusBar().showMessage(f"Opened {path.name}")
        self._add_recent_project_path(path)

    def _save_project_to_path(self, path: Path) -> None:
        self.project = self._project_from_controls()
        self._log_validation_messages(self.project)
        save_project(self.project, path)
        self.current_project_path = path
        self._populate_project_tree()
        self._populate_project_inspector()
        self._append_log(f"Saved project: {path}")
        self.statusBar().showMessage(f"Saved {path.name}")
        self._add_recent_project_path(path)

    def _load_recent_project_paths(self) -> list[Path]:
        raw_paths = self.settings.value("recentProjects", [])
        if isinstance(raw_paths, str):
            raw_paths = [raw_paths]
        return [Path(path) for path in raw_paths if str(path)]

    def _add_recent_project_path(self, path: Path) -> None:
        resolved = Path(path)
        paths = [item for item in self.recent_project_paths if item != resolved]
        self.recent_project_paths = [resolved, *paths][:5]
        self.settings.setValue("recentProjects", [str(item) for item in self.recent_project_paths])
        self._refresh_recent_project_actions()

    def _refresh_recent_project_actions(self) -> None:
        if not hasattr(self, "recent_menu"):
            return
        self.recent_menu.clear()
        if not self.recent_project_paths:
            empty = QAction("No recent projects", self)
            empty.setEnabled(False)
            self.recent_menu.addAction(empty)
            return
        for path in self.recent_project_paths:
            action = QAction(path.name, self)
            action.setToolTip(str(path))
            action.triggered.connect(lambda _checked=False, item=path: self._open_project_from_path(item))
            self.recent_menu.addAction(action)

    def _save_result_to_directory(self, directory: Path) -> Path:
        if self.current_result is None:
            raise RuntimeError("No simulation result is available")
        manifest = save_simulation_result(self.current_result, directory)
        self._append_log(f"Saved result: {manifest}")
        self.statusBar().showMessage(f"Saved result {directory.name}")
        self._populate_project_tree()
        return manifest

    def _sync_controls_from_project(self, project: Project) -> None:
        self.reactor_kind.setCurrentText(project.reactor.kind)
        self.nmax.setValue(project.reactor.nmax)
        self.t_final.setValue(project.recipe.integration.t_final)
        self.run_to_time_input.setValue(project.recipe.integration.t_final)
        self.backend.setCurrentText(project.recipe.integration.backend)
        self.simulation_mode.setCurrentText(project.recipe.integration.simulation_mode)
        self.include_monte_carlo.setChecked(project.recipe.integration.include_monte_carlo)
        self.use_tau_leaping.setChecked(project.recipe.integration.use_tau_leaping)
        self.galerkin_cells.setValue(project.recipe.integration.galerkin_cells)
        self.galerkin_degree.setValue(project.recipe.integration.galerkin_degree)
        self.kp.setValue(project.kinetics.kp)
        self.kt.setValue(project.kinetics.kt)
        self.kd.setValue(project.kinetics.kd)
        self.monomer.setValue(project.recipe.initial.monomer)
        self.initiator.setValue(project.recipe.initial.initiator)
        self.feed_rate.setValue(project.recipe.feed.rate)
        self.residence_time.setValue(project.reactor.residence_time)
        self.stages.setValue(project.reactor.stages)
        self.axial_cells.setValue(project.reactor.axial_cells)
        self._populate_recipe_table()
        self._populate_component_tables()
        self._populate_chart_administration()

    def _populate_project_tree(self) -> None:
        self.project_tree.clear()
        root = QTreeWidgetItem([self.project.name])
        items = {
            "Units": [self.project.recipe.unit_system],
            "Substances": [item.get("name", "substance") for item in self.project.substances],
            "Polymers": [item.get("name", "polymer") for item in self.project.polymers],
            "Reaction Groups": [step.name for step in self.project.reaction_steps],
            "Reactors": [self.project.reactor.kind],
            "Recipes": [self.project.recipe.name],
            "Outputs": list(self.project.outputs.enabled_generic_outputs),
            "Experiments": [],
            "Results": ["latest"] if self.current_result is not None else [],
        }
        for name, children in items.items():
            node = QTreeWidgetItem([name])
            for child in children:
                node.addChild(QTreeWidgetItem([str(child)]))
            root.addChild(node)
        self.project_tree.addTopLevelItem(root)
        root.setExpanded(True)
        self._populate_reaction_table()
        self._populate_recipe_table()
        self._populate_component_tables()

    def _populate_component_tables(self) -> None:
        if not hasattr(self, "substance_table"):
            return
        self.substance_table.setRowCount(len(self.project.substances))
        for row, item in enumerate(self.project.substances):
            values = [
                item.get("name", ""),
                item.get("alias", ""),
                item.get("kind", "species"),
                item.get("molecular_weight", 0.0),
                item.get("density", 0.0),
                item.get("is_monomer", False),
                item.get("phase_setting", "main"),
                item.get("density_mode", "linear"),
                item.get("density_linear_a", item.get("density", 0.0)),
                item.get("density_linear_b", 0.0),
                self._format_coeffs(item.get("heat_capacity_coeffs", (0.0, 0.0, 0.0, 0.0))),
                item.get("heat_capacity_kelvin", True),
            ]
            for column, value in enumerate(values):
                self.substance_table.setItem(row, column, QTableWidgetItem(str(value)))
        self.polymer_table.setRowCount(len(self.project.polymers))
        for row, item in enumerate(self.project.polymers):
            values = [
                item.get("name", ""),
                item.get("alias", ""),
                item.get("base_monomer", ""),
                item.get("active", False),
                item.get("dead", True),
                item.get("molecular_weight", 0.0),
                item.get("density", 0.0),
                item.get("phase_setting", "main"),
                item.get("density_mode", "linear"),
                item.get("density_linear_a", item.get("density", 0.0)),
                item.get("density_linear_b", 0.0),
                self._format_coeffs(item.get("heat_capacity_coeffs", (0.0, 0.0, 0.0, 0.0))),
                item.get("heat_capacity_kelvin", True),
            ]
            for column, value in enumerate(values):
                self.polymer_table.setItem(row, column, QTableWidgetItem(str(value)))
        self.parameter_table.setRowCount(len(self.project.parameters))
        for row, parameter in enumerate(self.project.parameters):
            values = [parameter.name, parameter.value, parameter.unit, parameter.kind, parameter.activation_energy or ""]
            for column, value in enumerate(values):
                self.parameter_table.setItem(row, column, QTableWidgetItem(str(value)))

    def _populate_reaction_table(self) -> None:
        if not hasattr(self, "reaction_table"):
            return
        self.reaction_table.setRowCount(len(self.project.reaction_steps))
        for row, step in enumerate(self.project.reaction_steps):
            values = [
                "yes" if step.enabled else "no",
                step.name,
                step.kind.value,
                step.site,
                ";".join(step.reactants),
                ";".join(step.products),
                step.rate_law.expression,
            ]
            for column, value in enumerate(values):
                self.reaction_table.setItem(row, column, QTableWidgetItem(value))

    def _populate_reaction_pattern_catalog_table(self) -> None:
        if not hasattr(self, "reaction_pattern_catalog_table"):
            return
        patterns = reaction_pattern_catalog()
        self.reaction_pattern_catalog_table.setRowCount(len(patterns))
        for row, pattern in enumerate(patterns):
            values = [
                pattern.name,
                pattern.category,
                pattern.kind.value if pattern.kind is not None else "general",
                ";".join(pattern.reactant_slots),
                ";".join(pattern.product_slots),
                ";".join(pattern.parameter_slots),
                "yes" if pattern.category in {"flow", "phase", "profile"} else "no",
                pattern.description,
            ]
            for column, value in enumerate(values):
                self.reaction_pattern_catalog_table.setItem(row, column, QTableWidgetItem(value))

    def _update_reaction_pattern_preview(self) -> None:
        if not hasattr(self, "reaction_pattern_preview"):
            return
        pattern_name = self.reaction_pattern_selector.currentText()
        pattern = next((item for item in reaction_pattern_catalog() if item.name == pattern_name), None)
        if pattern is None:
            self.reaction_pattern_preview.setText("")
            return
        reactants = " + ".join(pattern.reactant_slots) or "-"
        products = " + ".join(pattern.product_slots) or "-"
        parameters = ", ".join(pattern.parameter_slots) or "-"
        self.reaction_pattern_preview.setText(
            f"{pattern.name}: {reactants} -> {products} | parameters: {parameters} | {pattern.description}"
        )

    def _populate_reaction_pattern_slots(self) -> None:
        if not hasattr(self, "reaction_pattern_slot_table"):
            return
        pattern_name = self.reaction_pattern_selector.currentText()
        pattern = next((item for item in reaction_pattern_catalog() if item.name == pattern_name), None)
        if pattern is None:
            self.reaction_pattern_slot_table.setRowCount(0)
            return
        defaults = self._default_pattern_bindings(pattern.name)
        rows: list[tuple[str, str, str]] = []
        for index, slot in enumerate(pattern.reactant_slots):
            value = defaults[0][index] if index < len(defaults[0]) else slot
            rows.append(("reactant", slot, value))
        for index, slot in enumerate(pattern.product_slots):
            value = defaults[1][index] if index < len(defaults[1]) else slot
            rows.append(("product", slot, value))
        for index, slot in enumerate(pattern.parameter_slots):
            value = defaults[2] if index == 0 else slot
            rows.append(("parameter", slot, value))
        self.reaction_pattern_slot_table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                if column < 2:
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.reaction_pattern_slot_table.setItem(row, column, item)

    def _pattern_bindings_from_slot_table(self) -> tuple[tuple[str, ...], tuple[str, ...], str]:
        reactants: list[str] = []
        products: list[str] = []
        parameter = ""
        for row in range(self.reaction_pattern_slot_table.rowCount()):
            slot_type = self._table_text(self.reaction_pattern_slot_table, row, 0).strip()
            value = self._table_text(self.reaction_pattern_slot_table, row, 2).strip()
            if not value:
                continue
            if slot_type == "reactant":
                reactants.append(value)
            elif slot_type == "product":
                products.append(value)
            elif slot_type == "parameter" and not parameter:
                parameter = value
        if not reactants or not products or not parameter:
            return self._default_pattern_bindings(self.reaction_pattern_selector.currentText())
        return tuple(reactants), tuple(products), parameter

    def _add_default_reaction_step(self) -> None:
        self._add_reaction_step(ReactionKind.PROPAGATION)

    def _add_selected_reaction_step(self) -> None:
        self._add_reaction_step(ReactionKind(self.reaction_kind_selector.currentText()))

    def _add_selected_reaction_pattern(self) -> None:
        self._record_project_edit()
        pattern_name = self.reaction_pattern_selector.currentText()
        reactants, products, parameter = self._pattern_bindings_from_slot_table()
        self.project = build_polymer_reaction_step(
            self.project,
            pattern_name=pattern_name,
            reactants=reactants,
            products=products,
            parameter=parameter,
            site="default",
        )
        self._populate_project_tree()
        self._populate_project_inspector()
        self._append_log(f"Added reaction pattern: {pattern_name}")

    @staticmethod
    def _default_pattern_bindings(pattern_name: str) -> tuple[tuple[str, ...], tuple[str, ...], str]:
        defaults = {
            "Propagation": (("R", "M"), ("R",), "GP_kp"),
            "TerminationCombination": (("R", "R"), ("P",), "GP_ktc"),
            "TerminationDisproportionation": (("R", "R"), ("P", "P"), "GP_ktd"),
            "ChainTransfer": (("R", "CTA"), ("P", "R_new"), "GP_cta"),
        }
        return defaults.get(pattern_name, (("R", "M"), ("R",), "GP_k"))

    def _add_component_substance_row(self) -> None:
        row = self.substance_table.rowCount()
        self.substance_table.insertRow(row)
        for column, value in enumerate((f"S{row + 1}", "", "species", "0.0", "0.0", "False", "main", "linear", "0.0", "0.0", "0;0;0;0", "True")):
            self.substance_table.setItem(row, column, QTableWidgetItem(value))

    def _add_component_polymer_row(self) -> None:
        row = self.polymer_table.rowCount()
        self.polymer_table.insertRow(row)
        for column, value in enumerate((f"P{row + 1}", "", "", "True", "False", "0.0", "0.0", "main", "linear", "0.0", "0.0", "0;0;0;0", "True")):
            self.polymer_table.setItem(row, column, QTableWidgetItem(value))

    def _add_component_parameter_row(self) -> None:
        row = self.parameter_table.rowCount()
        self.parameter_table.insertRow(row)
        for column, value in enumerate((f"k{row + 1}", "0.0", "", "scalar", "")):
            self.parameter_table.setItem(row, column, QTableWidgetItem(value))

    def _apply_component_tables(self) -> None:
        self._record_project_edit()
        project = Project(
            schema_version=self.project.schema_version,
            name=self.project.name,
            reactor=self.project.reactor,
            kinetics=self.project.kinetics,
            recipe=self.project.recipe,
            outputs=self.project.outputs,
            heat_balance=self.project.heat_balance,
            reaction_steps=list(self.project.reaction_steps),
            general_kinetic_steps=list(self.project.general_kinetic_steps),
            general_initial_conditions=dict(self.project.general_initial_conditions),
            generic_parameters=dict(self.project.generic_parameters),
            parameters=[],
            reaction_modifier_scripts=dict(self.project.reaction_modifier_scripts),
        )
        for row in range(self.substance_table.rowCount()):
            name = self._table_text(self.substance_table, row, 0).strip()
            if not name:
                continue
            project = add_substance(
                project,
                Substance(
                    name=name,
                    alias=self._table_text(self.substance_table, row, 1).strip(),
                    kind=self._table_text(self.substance_table, row, 2).strip() or "species",
                    molecular_weight=self._table_float(self.substance_table, row, 3, 0.0),
                    density=self._table_float(self.substance_table, row, 4, 0.0),
                    is_monomer=self._table_bool(self.substance_table, row, 5),
                    phase_setting=self._table_text(self.substance_table, row, 6).strip() or "main",
                    density_mode=self._table_text(self.substance_table, row, 7).strip() or "linear",
                    density_linear_a=self._table_float(self.substance_table, row, 8, 0.0),
                    density_linear_b=self._table_float(self.substance_table, row, 9, 0.0),
                    heat_capacity_coeffs=self._parse_coeffs(self._table_text(self.substance_table, row, 10)),
                    heat_capacity_kelvin=self._table_bool(self.substance_table, row, 11),
                ),
            )
        for row in range(self.polymer_table.rowCount()):
            name = self._table_text(self.polymer_table, row, 0).strip()
            if not name:
                continue
            project = add_polymer_species(
                project,
                PolymerSpecies(
                    name=name,
                    alias=self._table_text(self.polymer_table, row, 1).strip(),
                    base_monomer=self._table_text(self.polymer_table, row, 2).strip(),
                    active=self._table_bool(self.polymer_table, row, 3),
                    dead=self._table_bool(self.polymer_table, row, 4),
                    molecular_weight=self._table_float(self.polymer_table, row, 5, 0.0),
                    density=self._table_float(self.polymer_table, row, 6, 0.0),
                    phase_setting=self._table_text(self.polymer_table, row, 7).strip() or "main",
                    density_mode=self._table_text(self.polymer_table, row, 8).strip() or "linear",
                    density_linear_a=self._table_float(self.polymer_table, row, 9, 0.0),
                    density_linear_b=self._table_float(self.polymer_table, row, 10, 0.0),
                    heat_capacity_coeffs=self._parse_coeffs(self._table_text(self.polymer_table, row, 11)),
                    heat_capacity_kelvin=self._table_bool(self.polymer_table, row, 12),
                ),
            )
        for row in range(self.parameter_table.rowCount()):
            name = self._table_text(self.parameter_table, row, 0).strip()
            if not name:
                continue
            activation = self._table_text(self.parameter_table, row, 4).strip()
            project = add_parameter(
                project,
                Parameter(
                    name=name,
                    value=self._table_float(self.parameter_table, row, 1, 0.0),
                    unit=self._table_text(self.parameter_table, row, 2).strip(),
                    kind=self._table_text(self.parameter_table, row, 3).strip() or "scalar",
                    activation_energy=None if not activation else float(activation),
                ),
            )
        self.project = project
        self._populate_project_tree()
        self._populate_project_inspector()
        self._append_log("Applied component tables")

    def _add_reaction_step(self, kind: ReactionKind) -> None:
        self._record_project_edit()
        parameter = {
            ReactionKind.PROPAGATION: "GP_kp",
            ReactionKind.TERMINATION_DISPROPORTIONATION: "GP_kt",
            ReactionKind.TERMINATION_COMBINATION: "GP_kt",
            ReactionKind.CHAIN_TRANSFER_TO_MONOMER: "GP_ctr",
            ReactionKind.CHAIN_TRANSFER_TO_AGENT: "GP_cta",
            ReactionKind.SCISSION: "GP_ks",
        }.get(kind, "GP_k")
        step = ReactionStep(
            name=f"{kind.value}_{len(self.project.reaction_steps) + 1}",
            kind=kind,
            reactants=("R", "M"),
            products=("R",),
            rate_law=RateLaw(parameter, (parameter,)),
        )
        parameter_value = self.project.generic_parameters.get(parameter, self.project.kinetics.kp)
        self.project = Project(
            schema_version=self.project.schema_version,
            name=self.project.name,
            reactor=self.project.reactor,
            kinetics=self.project.kinetics,
            recipe=self.project.recipe,
            outputs=self.project.outputs,
            heat_balance=self.project.heat_balance,
            substances=list(self.project.substances),
            polymers=list(self.project.polymers),
            reaction_steps=[*self.project.reaction_steps, step],
            generic_parameters={**self.project.generic_parameters, parameter: parameter_value},
            parameters=list(self.project.parameters),
            reaction_modifier_scripts=dict(self.project.reaction_modifier_scripts),
        )
        self._populate_project_tree()
        self._populate_project_inspector()

    def _remove_selected_reaction_step(self) -> None:
        row = self.reaction_table.currentRow()
        if row < 0:
            return
        self._record_project_edit()
        steps = [step for index, step in enumerate(self.project.reaction_steps) if index != row]
        self.project = Project(
            schema_version=self.project.schema_version,
            name=self.project.name,
            reactor=self.project.reactor,
            kinetics=self.project.kinetics,
            recipe=self.project.recipe,
            outputs=self.project.outputs,
            heat_balance=self.project.heat_balance,
            substances=list(self.project.substances),
            polymers=list(self.project.polymers),
            reaction_steps=steps,
            generic_parameters=dict(self.project.generic_parameters),
            parameters=list(self.project.parameters),
            reaction_modifier_scripts=dict(self.project.reaction_modifier_scripts),
        )
        self._populate_project_tree()
        self._populate_project_inspector()

    def _apply_reaction_table_edits(self) -> None:
        self._record_project_edit()
        steps: list[ReactionStep] = []
        generic_parameters = dict(self.project.generic_parameters)
        for row in range(self.reaction_table.rowCount()):
            step = self._reaction_step_from_table_row(row)
            steps.append(step)
            for parameter in step.rate_law.parameters:
                generic_parameters.setdefault(parameter, self.project.kinetics.kp)
        self.project = Project(
            schema_version=self.project.schema_version,
            name=self.project.name,
            reactor=self.project.reactor,
            kinetics=self.project.kinetics,
            recipe=self.project.recipe,
            outputs=self.project.outputs,
            heat_balance=self.project.heat_balance,
            substances=list(self.project.substances),
            polymers=list(self.project.polymers),
            reaction_steps=steps,
            generic_parameters=generic_parameters,
            parameters=list(self.project.parameters),
            reaction_modifier_scripts=dict(self.project.reaction_modifier_scripts),
        )
        self._populate_project_tree()
        self._populate_project_inspector()
        self._append_log("Applied reaction table edits")

    def _apply_reaction_modifier_to_selected_step(self) -> None:
        if self.reaction_table.rowCount() == 0:
            return
        row = self.reaction_table.currentRow()
        if row < 0:
            row = self.reaction_table.rowCount() - 1
        expression = self.reaction_modifier_expression.currentText().strip()
        script = self.reaction_modifier_script.toPlainText().strip()
        try:
            modifier = parse_reaction_rate_modifier(expression)
        except ValueError as exc:
            QMessageBox.critical(self, "Modifier failed", str(exc))
            return
        if not script:
            QMessageBox.critical(self, "Modifier failed", "Modifier script is required")
            return
        if self.reaction_table.item(row, 6) is None:
            self.reaction_table.setItem(row, 6, QTableWidgetItem(expression))
        else:
            self.reaction_table.item(row, 6).setText(expression)
        self._record_project_edit()
        steps = [
            self._reaction_step_from_table_row(index)
            for index in range(self.reaction_table.rowCount())
        ]
        generic_parameters = dict(self.project.generic_parameters)
        generic_parameters.setdefault(modifier.parameter, self.project.kinetics.kp)
        self.project = Project(
            schema_version=self.project.schema_version,
            name=self.project.name,
            reactor=self.project.reactor,
            kinetics=self.project.kinetics,
            recipe=self.project.recipe,
            outputs=self.project.outputs,
            heat_balance=self.project.heat_balance,
            substances=list(self.project.substances),
            polymers=list(self.project.polymers),
            reaction_steps=steps,
            generic_parameters=generic_parameters,
            parameters=list(self.project.parameters),
            reaction_modifier_scripts={
                **self.project.reaction_modifier_scripts,
                modifier.script_name: script,
            },
        )
        self._populate_project_tree()
        self._populate_project_inspector()
        self._append_log(f"Applied reaction modifier: {expression}")

    def _reaction_step_from_table_row(self, row: int) -> ReactionStep:
        enabled = self._table_text(self.reaction_table, row, 0).strip().lower() not in {"", "0", "false", "no", "off"}
        name = self._table_text(self.reaction_table, row, 1).strip() or f"reaction_{row + 1}"
        kind_text = self._table_text(self.reaction_table, row, 2).strip() or ReactionKind.PROPAGATION.value
        site = self._table_text(self.reaction_table, row, 3).strip() or "default"
        reactants = self._split_species(self._table_text(self.reaction_table, row, 4))
        products = self._split_species(self._table_text(self.reaction_table, row, 5))
        rate = self._table_text(self.reaction_table, row, 6).strip() or "0.0"
        parameters = self._rate_law_parameters(rate)
        return ReactionStep(
            name=name,
            kind=ReactionKind(kind_text),
            reactants=reactants,
            products=products,
            rate_law=RateLaw(rate, parameters),
            enabled=enabled,
            site=site,
        )

    @staticmethod
    def _rate_law_parameters(rate: str) -> tuple[str, ...]:
        if not rate.startswith("GP_"):
            return ()
        try:
            return (parse_reaction_rate_modifier(rate).parameter,)
        except ValueError:
            return (rate,)

    @staticmethod
    def _table_text(table: QTableWidget, row: int, column: int) -> str:
        item = table.item(row, column)
        return item.text() if item is not None else ""

    @classmethod
    def _table_float(cls, table: QTableWidget, row: int, column: int, default: float) -> float:
        text = cls._table_text(table, row, column).strip()
        return default if not text else float(text)

    @classmethod
    def _table_bool(cls, table: QTableWidget, row: int, column: int) -> bool:
        return cls._table_text(table, row, column).strip().lower() in {"1", "true", "yes", "on"}

    @staticmethod
    def _format_coeffs(values: object) -> str:
        if isinstance(values, str):
            return values
        try:
            return ";".join(str(float(value)) for value in values)  # type: ignore[union-attr]
        except TypeError:
            return "0;0;0;0"

    @staticmethod
    def _parse_coeffs(value: str) -> tuple[float, float, float, float]:
        parts = [part.strip() for part in value.replace(",", ";").split(";") if part.strip()]
        numbers = []
        for part in parts[:4]:
            try:
                numbers.append(float(part))
            except ValueError:
                numbers.append(0.0)
        while len(numbers) < 4:
            numbers.append(0.0)
        return tuple(numbers)  # type: ignore[return-value]

    @staticmethod
    def _split_species(value: str) -> tuple[str, ...]:
        return tuple(part.strip() for part in value.split(";") if part.strip())

    def _populate_project_inspector(self) -> None:
        messages = validate_project(self.project)
        summary = validation_summary(messages)
        values: dict[str, object] = {
            "project": self.project.name,
            "schema": self.project.schema_version,
            "reactor": self.project.reactor.kind,
            "recipe": self.project.recipe.name,
            "unit system": self.project.recipe.unit_system,
            "path": self.current_project_path or "<unsaved>",
            "validation errors": summary["errors"],
            "validation warnings": summary["warnings"],
        }
        for index, message in enumerate(messages[:8], start=1):
            values[f"{message.severity} {index}"] = f"{message.path}: {message.message}"
        self._populate_inspector(values)
        self._style_validation_rows()

    def _style_validation_rows(self) -> None:
        for row in range(self.inspector.rowCount()):
            key_item = self.inspector.item(row, 0)
            if key_item is None:
                continue
            key = key_item.text()
            color = None
            if key.startswith("error "):
                color = QColor("#fee2e2")
            elif key.startswith("warning "):
                color = QColor("#fef3c7")
            elif key in {"validation errors", "validation warnings"}:
                try:
                    count = int(float(self.inspector.item(row, 1).text()))
                except (AttributeError, ValueError):
                    count = 0
                if count > 0:
                    color = QColor("#fee2e2" if key.endswith("errors") else "#fef3c7")
            if color is None:
                continue
            for column in range(self.inspector.columnCount()):
                item = self.inspector.item(row, column)
                if item is not None:
                    item.setBackground(color)

    def _log_validation_messages(self, project: Project) -> None:
        messages = validate_project(project)
        if not messages:
            return
        summary = validation_summary(messages)
        self._append_log(f"Validation: {summary['errors']} errors, {summary['warnings']} warnings")
        for message in messages[:5]:
            self._append_log(f"{message.severity.upper()} {message.path}: {message.message}")

    def _apply_stylesheet(self) -> None:
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background: #f5f6f7; color: #17212b; font-size: 12px; }
            QMenuBar, QToolBar, QStatusBar { background: #ffffff; border-bottom: 1px solid #d6dbe0; }
            QDockWidget::title { background: #e8edf2; padding: 5px; font-weight: 600; }
            QGroupBox { border: 1px solid #c8d0d8; border-radius: 6px; margin-top: 12px; padding: 8px; font-weight: 600; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
            QPushButton { background: #26547c; color: white; border: 0; border-radius: 5px; padding: 6px 10px; }
            QPushButton:hover { background: #1d425f; }
            QTableWidget, QTreeWidget, QPlainTextEdit { background: #ffffff; border: 1px solid #ccd4dc; gridline-color: #e1e6eb; }
            QHeaderView::section { background: #eef2f5; border: 0; border-right: 1px solid #d6dbe0; padding: 5px; font-weight: 600; }
            QTabWidget::pane { border: 1px solid #ccd4dc; background: #ffffff; }
            QTabBar::tab { background: #e8edf2; padding: 7px 12px; border: 1px solid #ccd4dc; border-bottom: 0; }
            QTabBar::tab:selected { background: #ffffff; }
            QLabel#DashboardSummary { background: #ffffff; border: 1px solid #ccd4dc; border-radius: 6px; padding: 10px; font-weight: 600; }
            """
        )

    @staticmethod
    def _spin(minimum: int, maximum: int, value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        return spin

    @staticmethod
    def _double_spin(minimum: float, maximum: float, value: float) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        spin.setDecimals(6)
        spin.setSingleStep(max(value * 0.1, 0.01))
        return spin
