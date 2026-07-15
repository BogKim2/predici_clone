from predici_clone.api import (
    Parameter,
    PolymerSpecies,
    Project,
    Substance,
    add_parameter,
    add_polymer_species,
    add_substance,
    auto_declare_components,
    component_references,
    parameter_value,
)
from predici_clone.api.project_schema import GeneralKineticParticipant, GeneralKineticStep


def test_component_schema_round_trips_through_project_dict():
    project = Project()
    project = add_substance(
        project,
        Substance(
            "MMA",
            alias="M",
            molecular_weight=100.12,
            is_monomer=True,
            phase_setting="own",
            density_linear_a=940.0,
            density_linear_b=0.75,
            heat_capacity_coeffs=(1.0, 2.0, 3.0, 4.0),
        ),
    )
    project = add_polymer_species(
        project,
        PolymerSpecies(
            "PMMA*",
            base_monomer="MMA",
            active=True,
            dead=False,
            phase_setting="reactive",
            density_linear_a=1100.0,
        ),
    )
    project = add_parameter(project, Parameter("kp", value=0.12, unit="L/mol/s", kind="Arrhenius", pre_exponential=1.0e5))
    project = Project.from_dict(
        {
            **project.to_dict(),
            "reaction_modifier_scripts": {"File": 'result = getkp("kp")'},
        }
    )

    loaded = Project.from_dict(project.to_dict())

    assert loaded.substances[0]["name"] == "MMA"
    assert loaded.substances[0]["phase_setting"] == "own"
    assert loaded.substances[0]["density_linear_b"] == 0.75
    assert tuple(loaded.substances[0]["heat_capacity_coeffs"]) == (1.0, 2.0, 3.0, 4.0)
    assert loaded.polymers[0]["active"] is True
    assert loaded.polymers[0]["phase_setting"] == "reactive"
    assert loaded.parameters[0].name == "kp"
    assert loaded.parameters[0].pre_exponential == 1.0e5
    assert loaded.generic_parameters["kp"] == 0.12
    assert loaded.reaction_modifier_scripts["File"] == 'result = getkp("kp")'


def test_auto_declare_components_adds_numeric_constants_and_scalars():
    project = auto_declare_components(
        Project(),
        species_names=("A", "B"),
        polymer_names=("P*",),
        parameter_names=("0", "k1"),
    )

    assert [item["name"] for item in project.substances] == ["A", "B"]
    assert project.polymers[0]["name"] == "P*"
    assert parameter_value(project, "0") == 0.0
    assert parameter_value(project, "k1") == 0.0
    assert {parameter.name: parameter.kind for parameter in project.parameters}["0"] == "numeric_constant"


def test_component_references_reports_reaction_and_general_kinetic_uses():
    project = Project(
        general_kinetic_steps=[
            GeneralKineticStep(
                "r1",
                reactants=(GeneralKineticParticipant("A"),),
                products=(GeneralKineticParticipant("B"),),
                forward_parameter="k1",
            )
        ]
    )

    assert component_references(project, "A")["species"] == ["general_kinetic_steps[0].r1"]
    assert component_references(project, "k1")["parameters"] == ["general_kinetic_steps[0].r1"]
