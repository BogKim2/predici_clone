import pytest

from predici_clone.api import (
    Project,
    RecipeComponent,
    add_feed_tank,
    fill_remainder,
    load_project,
    make_concentration_consistent,
    normalize_recipe_components,
    save_project,
)
from predici_clone.api.recipe_consistency import consistency_sum


def _components():
    return (
        RecipeComponent("M", molecular_weight=100.0, density=800.0, mass=80.0, mass_part=0.8, moles=0.8, mole_part=0.5),
        RecipeComponent("S", molecular_weight=50.0, density=1000.0, mass=20.0, mass_part=0.2, moles=0.4, mole_part=0.5),
    )


@pytest.mark.parametrize(
    ("mode", "kwargs"),
    [
        ("absolute_mass", {}),
        ("mass_part_total_mass", {"total_mass": 100.0}),
        ("absolute_mole", {}),
        ("mole_part", {"total_moles": 1.2}),
        ("concentration_and_volume", {"volume": 1.0}),
        ("mass_part_total_mole", {"total_moles": 1.2}),
        ("mole_part_total_mass", {"total_mass": 100.0}),
    ],
)
def test_recipe_input_modes_normalize_to_consistent_table(mode, kwargs):
    rows = _components()
    if mode == "concentration_and_volume":
        rows = (
            RecipeComponent("M", molecular_weight=100.0, density=800.0, concentration=0.8),
            RecipeComponent("S", molecular_weight=50.0, density=1000.0, concentration=0.4),
        )

    composition = normalize_recipe_components(mode, rows, temperature=320.0, pressure=2.0, **kwargs)

    assert composition.mode == mode
    assert composition.total_mass > 0.0
    assert composition.total_moles > 0.0
    assert composition.volume > 0.0
    assert composition.temperature == 320.0
    assert composition.pressure == 2.0
    assert sum(component.mass_part for component in composition.components) == pytest.approx(1.0)
    assert sum(component.mole_part for component in composition.components) == pytest.approx(1.0)


def test_make_concentration_consistent_sets_target_from_density_rule():
    rows = (
        RecipeComponent("A", molecular_weight=100.0, density=800.0, concentration=4.0),
        RecipeComponent("B", molecular_weight=50.0, density=1000.0, concentration=0.0),
    )

    adjusted = make_concentration_consistent(rows, "B")

    assert consistency_sum(adjusted) == pytest.approx(1.0)
    assert adjusted[1].concentration == pytest.approx(10.0)


def test_fill_remainder_sets_rest_for_mass_or_mole_parts():
    rows = (
        RecipeComponent("M", molecular_weight=100.0, density=800.0, mass_part=0.7, mole_part=0.25),
        RecipeComponent("I", molecular_weight=200.0, density=900.0, mass_part=0.1, mole_part=0.25),
        RecipeComponent("S", molecular_weight=50.0, density=1000.0),
    )

    mass_adjusted = fill_remainder(rows, "S", field="mass_part")
    mole_adjusted = fill_remainder(rows, "S", field="mole_part")

    assert mass_adjusted[2].mass_part == pytest.approx(0.2)
    assert mole_adjusted[2].mole_part == pytest.approx(0.5)


def test_feed_tank_extended_fields_roundtrip(tmp_path):
    project = add_feed_tank(
        Project(),
        monomer=3.0,
        initiator=0.2,
        rate=0.1,
        temperature=315.0,
        time_profile=[{"time": 0.0, "mass_stream": 0.1, "temperature": 315.0}],
        use_feed_control=True,
        feed_control_script="result = 0.1",
        use_temperature_control=True,
        temperature_control_script="result = 315",
        switch_time=4.0,
    )
    path = tmp_path / "feed.predici.json"
    save_project(project, path)

    tank = load_project(path).recipe.feed_tanks[0]

    assert tank.feed_type == "mass_stream_simple"
    assert tank.temperature == 315.0
    assert tank.time_profile[0]["mass_stream"] == 0.1
    assert tank.use_feed_control is True
    assert tank.feed_control_script == "result = 0.1"
    assert tank.use_temperature_control is True
    assert tank.temperature_control_script == "result = 315"
    assert tank.switch_time == 4.0
