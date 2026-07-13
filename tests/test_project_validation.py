from predici_clone.api import (
    FRPParameters,
    HeatBalanceConfig,
    IntegrationControl,
    ProfilePoint,
    Project,
    ReactorConfig,
    Recipe,
    validate_project,
    validation_summary,
)
from predici_clone.kinetics import RateLaw, ReactionKind, ReactionStep


def test_validate_project_accepts_default_project():
    messages = validate_project(Project())

    assert validation_summary(messages) == {"errors": 0, "warnings": 0}


def test_validate_project_reports_invalid_numeric_and_backend_settings():
    project = Project(
        reactor=ReactorConfig(kind="CSTR", nmax=0),
        recipe=Recipe(integration=IntegrationControl(t_final=-1.0, output_points=0, backend="galerkin_direct")),
        kinetics=FRPParameters(kp=-0.1),
    )

    messages = validate_project(project)
    codes = {message.code for message in messages}

    assert "nmax_positive" in codes
    assert "t_final_positive" in codes
    assert "output_points_positive" in codes
    assert "kp_non_negative" in codes
    assert "galerkin_direct_batch_semibatch_only" not in codes
    assert validation_summary(messages)["errors"] >= 4


def test_validate_project_reports_profiles_heat_and_missing_generic_parameters():
    project = Project(
        recipe=Recipe(
            temperature_profile=[ProfilePoint(2.0, 310.0), ProfilePoint(1.0, 300.0)],
            pre_schedule=[{"time": 1.0, "action": "set_feed_rate", "rate": -0.1}],
        ),
        heat_balance=HeatBalanceConfig(enabled=True, use_heat_exchanger=True, heat_transfer=0.0, area=0.0),
        reaction_steps=[
            ReactionStep(
                name="prop",
                kind=ReactionKind.PROPAGATION,
                reactants=("R", "M"),
                products=("R",),
                rate_law=RateLaw("GP_missing", ("GP_missing",)),
            )
        ],
    )

    messages = validate_project(project)
    codes = {message.code for message in messages}

    assert "profile_time_increasing" in codes
    assert "schedule_rate_non_negative" in codes
    assert "inactive_heat_exchanger" in codes
    assert "missing_generic_parameter" in codes
    assert validation_summary(messages)["warnings"] >= 2


def test_validate_project_reports_invalid_polymer_feed():
    project = Project(recipe=Recipe(polymer_feed=[{"name": "bad", "rate": -1.0, "mass_fraction": 1.5, "Mn": -2.0, "Mw": -3.0}]))

    codes = {message.code for message in validate_project(project)}

    assert "polymer_feed_rate_non_negative" in codes
    assert "polymer_feed_fraction_range" in codes
    assert "polymer_feed_mn_non_negative" in codes
    assert "polymer_feed_mw_non_negative" in codes


def test_validate_project_accepts_temperature_and_pressure_schedule_actions():
    valid = Project(
        recipe=Recipe(
            pre_schedule=[
                {"time": 1.0, "action": "set_temperature", "value": 330.0},
                {"time": 2.0, "action": "set_pressure", "pressure": 3.0},
                {"time": 3.0, "action": "set_residence_time", "value": 2.0},
                {"time": 4.0, "action": "set_coolant_temperature", "temperature": 305.0},
                {"time": 5.0, "action": "set_additional_heat", "heat": 1.0},
            ]
        )
    )
    invalid = Project(recipe=Recipe(pre_schedule=[{"time": 1.0, "action": "set_pressure"}]))
    invalid_residence = Project(recipe=Recipe(pre_schedule=[{"time": 1.0, "action": "set_residence_time", "value": 0.0}]))
    invalid_thermal = Project(recipe=Recipe(pre_schedule=[{"time": 1.0, "action": "set_coolant_temperature"}]))

    valid_codes = {message.code for message in validate_project(valid)}
    invalid_codes = {message.code for message in validate_project(invalid)}
    invalid_residence_codes = {message.code for message in validate_project(invalid_residence)}
    invalid_thermal_codes = {message.code for message in validate_project(invalid_thermal)}

    assert "schedule_action_known" not in valid_codes
    assert "schedule_pressure_value_required" in invalid_codes
    assert "schedule_residence_time_positive" in invalid_residence_codes
    assert "schedule_coolant_temperature_value_required" in invalid_thermal_codes
