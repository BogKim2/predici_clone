from predici_clone.api import (
    IntegrationControl,
    OutputConfig,
    Project,
    ReactorConfig,
    Recipe,
    add_feed_tank,
    append_pre_schedule_step,
    apply_pre_schedule,
    effective_feed_stream,
    evaluate_profile,
    load_project,
    save_project,
    scheduled_pressure,
    scheduled_residence_time,
    scheduled_temperature,
    set_pressure_profile,
    set_temperature_profile,
)
from predici_clone.api.automation import get_reactor_pressure
from predici_clone.engine import SimulationEngine
from predici_clone.postprocess.generic_outputs import compute_generic_outputs


def test_recipe_profiles_roundtrip_and_interpolate(tmp_path):
    project = set_pressure_profile(
        set_temperature_profile(Project(), [(0.0, 300.0), (10.0, 340.0)]),
        [(0.0, 1.0), (10.0, 4.0)],
    )
    path = tmp_path / "profile.predici.json"
    save_project(project, path)
    loaded = load_project(path)

    assert evaluate_profile(loaded.recipe.temperature_profile, 5.0, 298.15) == 320.0
    assert evaluate_profile(loaded.recipe.pressure_profile, 5.0, 1.0) == 2.5


def test_pre_schedule_feed_rate_application_is_time_ordered():
    project = append_pre_schedule_step(Project(), 5.0, "set_feed_rate", rate=0.2)
    project = append_pre_schedule_step(project, 2.0, "set_feed_rate", rate=0.1)

    early = apply_pre_schedule(project, 1.0)
    late = apply_pre_schedule(project, 6.0)

    assert early.recipe.feed.rate == Project().recipe.feed.rate
    assert late.recipe.feed.rate == 0.2
    assert [step["time"] for step in project.recipe.pre_schedule] == [2.0, 5.0]


def test_multiple_feed_tanks_roundtrip_and_effective_feed(tmp_path):
    project = add_feed_tank(Project(), monomer=4.0, initiator=0.3, rate=0.04)
    path = tmp_path / "feed_tanks.predici.json"
    save_project(project, path)
    loaded = load_project(path)
    feed = effective_feed_stream(loaded.recipe)

    assert len(loaded.recipe.feed_tanks) == 1
    assert feed.rate == loaded.recipe.feed.rate + loaded.recipe.feed_tanks[0].rate
    assert feed.monomer > loaded.recipe.feed.monomer


def test_engine_exposes_recipe_profiles_as_outputs():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=20),
        recipe=Recipe(integration=IntegrationControl(t_final=2.0, output_points=5)),
        outputs=OutputConfig(enabled_generic_outputs=("temperature", "pressure", "feed_rate")),
    )
    project = set_temperature_profile(project, [(0.0, 300.0), (2.0, 330.0)])
    project = set_pressure_profile(project, [(0.0, 1.0), (2.0, 3.0)])
    project = append_pre_schedule_step(project, 1.0, "set_feed_rate", rate=0.15)

    result = SimulationEngine(project).run()
    outputs = compute_generic_outputs(result, project.outputs)

    assert result.metadata["temperature_setpoint_history"][-1] == 330.0
    assert get_reactor_pressure(result) == 3.0
    assert outputs["temperature"] == 330.0
    assert outputs["pressure"] == 3.0
    assert outputs["feed_rate"] == 0.15


def test_pre_schedule_temperature_and_pressure_override_profiles():
    project = Project(
        reactor=ReactorConfig(kind="Batch", nmax=20),
        recipe=Recipe(integration=IntegrationControl(t_final=3.0, output_points=6)),
        outputs=OutputConfig(enabled_generic_outputs=("temperature", "pressure")),
    )
    project = set_temperature_profile(project, [(0.0, 300.0), (3.0, 330.0)])
    project = set_pressure_profile(project, [(0.0, 1.0), (3.0, 2.0)])
    project = append_pre_schedule_step(project, 1.5, "set_temperature", value=345.0)
    project = append_pre_schedule_step(project, 2.0, "set_pressure", pressure=4.0)

    result = SimulationEngine(project).run()
    outputs = compute_generic_outputs(result, project.outputs)

    assert scheduled_temperature(project.recipe, 2.0, 298.15) == 345.0
    assert scheduled_pressure(project.recipe, 2.5, 1.0) == 4.0
    assert result.metadata["temperature_setpoint_history"][-1] == 345.0
    assert result.metadata["pressure_history"][-1] == 4.0
    assert outputs["temperature"] == 345.0
    assert outputs["pressure"] == 4.0


def test_pre_schedule_residence_time_updates_project_and_cstr_rhs():
    base = Project(
        reactor=ReactorConfig(kind="CSTR", nmax=20, residence_time=5.0),
        recipe=Recipe(integration=IntegrationControl(t_final=4.0, output_points=8)),
        outputs=OutputConfig(enabled_generic_outputs=("residence_time", "mass")),
    )
    scheduled = append_pre_schedule_step(base, 1.0, "set_residence_time", value=1.5)

    applied = apply_pre_schedule(scheduled, 2.0)
    base_result = SimulationEngine(base).run()
    scheduled_result = SimulationEngine(scheduled).run()
    outputs = compute_generic_outputs(scheduled_result, scheduled.outputs)

    assert applied.reactor.residence_time == 1.5
    assert scheduled_residence_time(scheduled.recipe, 2.0, base.reactor.residence_time) == 1.5
    assert scheduled_result.success
    assert scheduled_result.metadata["scheduled_final_residence_time"] == 1.5
    assert outputs["residence_time"] == 1.5
    assert abs(scheduled_result.final_moments.mass - base_result.final_moments.mass) > 1e-8


def test_engine_semibatch_pre_schedule_changes_integrated_volume():
    base = Project(
        reactor=ReactorConfig(kind="Semi-batch", nmax=20, volume=1.0),
        recipe=Recipe(integration=IntegrationControl(t_final=4.0, output_points=9)),
    )
    scheduled = append_pre_schedule_step(base, 2.0, "set_feed_rate", rate=0.3)

    base_result = SimulationEngine(base).run()
    scheduled_result = SimulationEngine(scheduled).run()

    assert base_result.success
    assert scheduled_result.success
    assert scheduled_result.state_history[-1, -1] > base_result.state_history[-1, -1]
    assert scheduled_result.metadata["scheduled_final_feed_rate"] == 0.3


def test_engine_uses_multiple_feed_tank_total_rate_for_semibatch():
    base = Project(
        reactor=ReactorConfig(kind="Semi-batch", nmax=20, volume=1.0),
        recipe=Recipe(integration=IntegrationControl(t_final=3.0, output_points=7)),
    )
    with_tank = add_feed_tank(base, monomer=5.0, initiator=0.2, rate=0.2)

    base_result = SimulationEngine(base).run()
    tank_result = SimulationEngine(with_tank).run()

    assert tank_result.success
    assert tank_result.state_history[-1, -1] > base_result.state_history[-1, -1]
    assert tank_result.metadata["scheduled_final_feed_rate"] > base.recipe.feed.rate
