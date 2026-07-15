import numpy as np

from predici_clone.api import (
    FRPParameters,
    FeedStream,
    HeatBalanceConfig,
    InitialConditions,
    IntegrationControl,
    OutputConfig,
    Project,
    ReactorConfig,
    Recipe,
    load_project,
    load_result_manifest,
    save_project,
    save_simulation_result,
)
from predici_clone.api.automation import (
    check_enthalpy,
    get_dist_moments,
    get_dist_points,
    set_dist_lumping,
    set_enthalpy,
    set_feed_rate,
    set_heat_exchanger,
)
from predici_clone.api.recipe_profiles import append_pre_schedule_step
from predici_clone.engine import SimulationCallbacks, SimulationEngine
from predici_clone.kinetics import RateLaw, ReactionKind, ReactionStep
from predici_clone.postprocess.generic_outputs import compute_generic_outputs


def test_project_roundtrip_and_engine_run(tmp_path):
    project = Project(
        name="roundtrip",
        reactor=ReactorConfig(kind="Semi-batch", nmax=40, volume=1.0),
        kinetics=FRPParameters(kp=0.05, kt=0.02, kd=0.03),
        recipe=Recipe(
            initial=InitialConditions(monomer=0.2, initiator=0.02),
            feed=FeedStream(monomer=2.0, initiator=0.1, rate=0.05),
            integration=IntegrationControl(t_final=3.0, output_points=12),
        ),
    )
    path = tmp_path / "project.predici.json"
    save_project(project, path)
    loaded = load_project(path)

    assert loaded.name == "roundtrip"
    assert loaded.reactor.kind == "Semi-batch"
    assert loaded.reactor.stages == 4
    assert loaded.recipe.feed.rate == 0.05

    result = SimulationEngine(loaded).run()
    assert result.success
    assert result.final_distribution.size == 41
    assert result.final_moments.m0 > 0.0


def test_project_roundtrip_preserves_reaction_steps(tmp_path):
    project = Project(
        reaction_steps=[
            ReactionStep(
                name="propagation_a",
                kind=ReactionKind.PROPAGATION,
                reactants=("R", "M"),
                products=("R",),
                rate_law=RateLaw("GP_kp * M * R", ("GP_kp",)),
                site="site_a",
            )
        ],
        generic_parameters={"GP_kp": 0.1},
    )
    path = tmp_path / "reaction_project.predici.json"
    save_project(project, path)
    loaded = load_project(path)

    assert loaded.reaction_steps[0].name == "propagation_a"
    assert loaded.reaction_steps[0].kind == ReactionKind.PROPAGATION
    assert loaded.reaction_steps[0].rate_law.parameters == ("GP_kp",)


def test_engine_callbacks_receive_progress_and_steps():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=25),
        recipe=Recipe(integration=IntegrationControl(t_final=1.0, output_points=6)),
    )
    progress = []
    steps = []

    result = SimulationEngine(project).run(
        callbacks=SimulationCallbacks(
            on_progress=progress.append,
            on_step=steps.append,
        )
    )

    assert result.success
    np.testing.assert_allclose(progress[-1], 1.0)
    assert len(steps) == 6
    assert {"time", "Mn", "Mw", "PDI", "progress"} <= set(steps[-1])


def test_generic_kinetic_parameters_affect_engine_result():
    base = Project(
        reactor=ReactorConfig(kind="Batch", nmax=30),
        recipe=Recipe(integration=IntegrationControl(t_final=2.0, output_points=8)),
    )
    faster = Project(
        reactor=base.reactor,
        recipe=base.recipe,
        kinetics=base.kinetics,
        generic_parameters={"GP_kp": base.kinetics.kp * 5.0},
    )

    base_result = SimulationEngine(base).run()
    faster_result = SimulationEngine(faster).run()

    assert faster_result.final_moments.mass > base_result.final_moments.mass


def test_project_reaction_steps_affect_engine_distribution():
    base = Project(
        reactor=ReactorConfig(kind="Batch", nmax=30),
        recipe=Recipe(integration=IntegrationControl(t_final=2.0, output_points=8)),
    )
    with_transfer = Project(
        reactor=base.reactor,
        recipe=base.recipe,
        kinetics=base.kinetics,
        reaction_steps=[
            ReactionStep(
                name="transfer",
                kind=ReactionKind.CHAIN_TRANSFER_TO_MONOMER,
                reactants=("R", "M"),
                products=("P0",),
                rate_law=RateLaw("GP_ctr", ("GP_ctr",)),
            )
        ],
        generic_parameters={"GP_ctr": 10.0},
    )

    base_result = SimulationEngine(base).run()
    transfer_result = SimulationEngine(with_transfer).run()

    assert transfer_result.metadata["reaction_steps_applied"] == 1
    assert transfer_result.final_distribution[0] > base_result.final_distribution[0]


def test_reaction_modifier_script_affects_engine_distribution():
    base = Project(
        reactor=ReactorConfig(kind="Batch", nmax=30),
        recipe=Recipe(integration=IntegrationControl(t_final=2.0, output_points=8)),
        reaction_steps=[
            ReactionStep(
                name="transfer",
                kind=ReactionKind.CHAIN_TRANSFER_TO_MONOMER,
                reactants=("R", "M"),
                products=("P0",),
                rate_law=RateLaw("GP_ctr(File)", ("GP_ctr",)),
            )
        ],
        generic_parameters={"GP_ctr": 0.0},
        reaction_modifier_scripts={"File": "result = 10.0"},
    )

    without_script = Project.from_dict(
        {
            **base.to_dict(),
            "reaction_modifier_scripts": {},
        }
    )

    scripted_result = SimulationEngine(base).run()
    inactive_result = SimulationEngine(without_script).run()

    assert scripted_result.metadata["reaction_steps_applied"] == 1
    assert scripted_result.metadata["reaction_modifier_events"]
    assert scripted_result.metadata["reaction_modifier_events"][0]["value"] == 10.0
    assert scripted_result.final_distribution[0] > inactive_result.final_distribution[0]


def test_automation_api_exposes_distribution_points_and_moments():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=20),
        recipe=Recipe(integration=IntegrationControl(t_final=1.0, output_points=5)),
    )
    result = SimulationEngine(project).run()

    points = get_dist_points(result, log_axis=True)
    moments = get_dist_moments(result)
    changed_feed = set_feed_rate(project, 0.25)
    lumped = set_dist_lumping(project, True)

    assert points.shape == (21, 2)
    assert {"M0", "M1", "M2", "M3", "Mn", "Mw", "Mz", "PDI", "AMW", "mass"} <= set(moments)
    assert changed_feed.recipe.feed.rate == 0.25
    assert lumped.generic_parameters["dist_lumping"] == 1.0


def test_heat_exchanger_settings_roundtrip_and_validate(tmp_path):
    project = set_heat_exchanger(
        Project(),
        use_heat_exchanger=True,
        heat_transfer=120.0,
        area=2.5,
        heat_capacity=4.18,
        mass_flow=1.2,
        mass_holdup=0.8,
        initial_feed_temp=310.0,
        coolant_temperature=305.0,
        additional_heat=1.5,
        counter_current=True,
    )
    path = tmp_path / "heat_project.predici.json"
    save_project(project, path)
    loaded = load_project(path)

    assert loaded.heat_balance.enabled
    assert loaded.heat_balance.use_heat_exchanger
    assert loaded.heat_balance.counter_current
    assert loaded.heat_balance.heat_transfer == 120.0
    assert loaded.heat_balance.coolant_temperature == 305.0
    assert loaded.heat_balance.additional_heat == 1.5
    assert check_enthalpy(loaded)


def test_set_enthalpy_enables_heat_balance_and_sets_generic_parameter():
    project = set_enthalpy(Project(), "propagation", "monomer", -42.0)

    assert project.heat_balance.enabled
    assert project.generic_parameters["reaction_enthalpy"] == -42.0
    assert project.generic_parameters["enthalpy:propagation:monomer"] == -42.0


def test_heat_balance_adds_temperature_and_heat_duty_outputs():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=25),
        recipe=Recipe(integration=IntegrationControl(t_final=2.0, output_points=8)),
        outputs=OutputConfig(enabled_generic_outputs=("temperature", "heat_duty")),
        heat_balance=HeatBalanceConfig(
            enabled=True,
            use_heat_exchanger=True,
            heat_transfer=2.0,
            area=1.5,
            heat_capacity=4.0,
            mass_holdup=2.0,
            initial_feed_temp=300.0,
        ),
        generic_parameters={"reaction_enthalpy": -50.0},
    )

    result = SimulationEngine(project).run()
    outputs = compute_generic_outputs(result, project.outputs)

    assert result.metadata["heat_balance"] == "lumped_ode"
    assert len(result.metadata["temperature_history"]) == result.time.size
    assert outputs["temperature"] >= 300.0
    assert "heat_duty" in outputs


def test_heat_balance_uses_scheduled_coolant_and_additional_heat_outputs():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=25),
        recipe=Recipe(integration=IntegrationControl(t_final=2.0, output_points=8)),
        outputs=OutputConfig(enabled_generic_outputs=("temperature", "coolant_temperature", "additional_heat")),
        heat_balance=HeatBalanceConfig(
            enabled=True,
            use_heat_exchanger=True,
            heat_transfer=2.0,
            area=1.5,
            heat_capacity=4.0,
            mass_holdup=2.0,
            initial_feed_temp=300.0,
            coolant_temperature=295.0,
            additional_heat=0.0,
        ),
        generic_parameters={"reaction_enthalpy": -20.0},
    )
    project = append_pre_schedule_step(project, 1.0, "set_coolant_temperature", value=310.0)
    project = append_pre_schedule_step(project, 1.2, "set_additional_heat", heat=3.0)

    result = SimulationEngine(project).run()
    outputs = compute_generic_outputs(result, project.outputs)

    assert result.metadata["coolant_temperature_history"][-1] == 310.0
    assert result.metadata["additional_heat_history"][-1] == 3.0
    assert outputs["coolant_temperature"] == 310.0
    assert outputs["additional_heat"] == 3.0


def test_coupled_thermal_batch_uses_temperature_dependent_kinetics():
    base = Project(
        reactor=ReactorConfig(kind="Batch", nmax=25),
        recipe=Recipe(integration=IntegrationControl(t_final=1.5, output_points=6)),
        outputs=OutputConfig(enabled_generic_outputs=("temperature", "mass")),
        heat_balance=HeatBalanceConfig(
            enabled=True,
            use_heat_exchanger=True,
            heat_transfer=0.5,
            area=1.0,
            heat_capacity=4.0,
            mass_holdup=2.0,
            initial_feed_temp=300.0,
            coolant_temperature=300.0,
        ),
        generic_parameters={
            "temperature_dependent_kinetics": 1.0,
            "reaction_enthalpy": -40.0,
            "activation_energy": 15000.0,
            "reference_temperature": 300.0,
        },
    )
    heated = append_pre_schedule_step(base, 0.5, "set_additional_heat", heat=5.0)

    base_result = SimulationEngine(base).run()
    heated_result = SimulationEngine(heated).run()
    outputs = compute_generic_outputs(heated_result, heated.outputs)

    assert heated_result.metadata["heat_balance"] == "coupled_thermal_rhs"
    assert heated_result.metadata["thermal_coupled"]
    assert len(heated_result.metadata["temperature_history"]) == heated_result.time.size
    assert outputs["temperature"] > 300.0
    assert heated_result.final_moments.mass != base_result.final_moments.mass


def _thermal_project(kind: str) -> Project:
    reactor = ReactorConfig(kind=kind, nmax=18, volume=1.0, residence_time=3.0, stages=3, axial_cells=3)
    return Project(
        reactor=reactor,
        recipe=Recipe(
            initial=InitialConditions(monomer=0.6, initiator=0.05, radicals=0.01),
            feed=FeedStream(monomer=2.0, initiator=0.1, rate=0.08),
            integration=IntegrationControl(t_final=1.2, output_points=5),
        ),
        outputs=OutputConfig(enabled_generic_outputs=("temperature", "mass")),
        heat_balance=HeatBalanceConfig(
            enabled=True,
            use_heat_exchanger=True,
            heat_transfer=0.4,
            area=1.0,
            heat_capacity=4.0,
            mass_holdup=2.0,
            initial_feed_temp=300.0,
            coolant_temperature=300.0,
        ),
        generic_parameters={
            "temperature_dependent_kinetics": 1.0,
            "reaction_enthalpy": -30.0,
            "activation_energy": 12000.0,
            "reference_temperature": 300.0,
        },
    )


def test_coupled_thermal_semibatch_cstr_cascade_and_pfr_run():
    for kind in ("Semi-batch", "CSTR", "Cascade", "PFR"):
        project = append_pre_schedule_step(_thermal_project(kind), 0.4, "set_additional_heat", heat=4.0)
        if kind in {"CSTR", "Cascade", "PFR"}:
            project = append_pre_schedule_step(project, 0.6, "set_residence_time", value=1.5)

        result = SimulationEngine(project).run()
        outputs = compute_generic_outputs(result, project.outputs)

        assert result.success
        assert result.reactor_kind == kind
        assert result.metadata["heat_balance"] == "coupled_thermal_rhs"
        assert result.metadata["thermal_coupled"]
        assert len(result.metadata["temperature_history"]) == result.time.size
        assert outputs["temperature"] > 300.0
        assert result.final_distribution.size == project.reactor.nmax + 1
        if kind in {"Cascade", "PFR"}:
            assert result.metadata["thermal_coupled_stages"] == 3


def test_simulation_result_can_be_saved_with_manifest(tmp_path):
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=15),
        recipe=Recipe(integration=IntegrationControl(t_final=1.0, output_points=4)),
    )
    result = SimulationEngine(project).run()
    manifest_path = save_simulation_result(result, tmp_path / "run_001")
    manifest = load_result_manifest(manifest_path)

    assert manifest["reactor_kind"] == "Batch"
    assert manifest["backend"] in {"discrete", "unknown"}
    assert manifest["files"]["history"] == "distribution_history.npz"
    assert (tmp_path / "run_001" / "distribution_history.npz").exists()
    assert (tmp_path / "run_001" / "distribution_final.csv").exists()
    assert (tmp_path / "run_001" / "moments.csv").exists()
