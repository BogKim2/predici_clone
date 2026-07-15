from __future__ import annotations

from predici_clone.api.project_schema import (
    FRPParameters,
    GeneralKineticParticipant,
    GeneralKineticStep,
    InitialConditions,
    IntegrationControl,
    OutputConfig,
    Project,
    Recipe,
    ReactorConfig,
)
from predici_clone.kinetics import RateLaw, ReactionKind, ReactionStep


def polyethylene_basic_project() -> Project:
    """Polyethylene homopolymerization tutorial project from Predici11_Tutorials."""

    return Project(
        name="Tutorial: Polyethylene Basic Model",
        reactor=ReactorConfig(kind="Batch", nmax=300, volume=1.0),
        kinetics=FRPParameters(kp=1.2e4, kt=4.5e8, kd=1.6e-2, initiator_efficiency=1.0),
        recipe=Recipe(
            name="polyethylene_basic",
            unit_system="g-l-s-bar",
            initial=InitialConditions(monomer=19.94, initiator=1.0068e-4, radicals=0.0),
            integration=IntegrationControl(t_final=0.1, output_points=24, method="BDF", rtol=1e-7, atol=1e-12),
        ),
        outputs=OutputConfig(enabled_generic_outputs=("Mn", "Mw", "PDI", "conversion", "mass")),
        substances=[
            {
                "name": "I",
                "alias": "initiator",
                "kind": "initiator",
                "molecular_weight": 146.32,
                "initial_concentration": 1.0068e-4,
            },
            {
                "name": "E",
                "alias": "ethene",
                "kind": "monomer",
                "molecular_weight": 28.0,
                "is_monomer": True,
                "initial_concentration": 19.94,
            },
        ],
        polymers=[
            {
                "name": "R",
                "alias": "radicals",
                "kind": "active_polymer",
                "molecular_weight": 28.0,
            },
            {
                "name": "P",
                "alias": "polymer",
                "kind": "dead_polymer",
                "molecular_weight": 28.0,
            },
        ],
        reaction_steps=[
            ReactionStep(
                name="initiator_decay",
                kind=ReactionKind.INITIATION,
                reactants=("I",),
                products=("R",),
                rate_law=RateLaw("kd * I", ("kd",)),
            ),
            ReactionStep(
                name="propagation",
                kind=ReactionKind.PROPAGATION,
                reactants=("R", "E"),
                products=("R",),
                rate_law=RateLaw("kp * E * R", ("kp",)),
            ),
            ReactionStep(
                name="termination_combination",
                kind=ReactionKind.TERMINATION_COMBINATION,
                reactants=("R", "R"),
                products=("P",),
                rate_law=RateLaw("ktc * R * R", ("ktc",)),
            ),
            ReactionStep(
                name="termination_disproportionation",
                kind=ReactionKind.TERMINATION_DISPROPORTIONATION,
                reactants=("R", "R"),
                products=("P", "P"),
                rate_law=RateLaw("ktd * R * R", ("ktd",)),
            ),
        ],
        generic_parameters={
            "kd": 1.6e-2,
            "kp": 1.2e4,
            "ktc": 2.25e8,
            "ktd": 2.25e8,
            "GP_kd": 1.6e-2,
            "GP_kp": 1.2e4,
            "GP_kt": 4.5e8,
            "GP_f": 1.0,
            "tutorial_temperature_c": 200.0,
            "tutorial_pressure_bar": 2000.0,
        },
    )


def oregonator_kinetics_project(*, corrected_order: bool = True) -> Project:
    """PRESTO-KINETICS Oregonator tutorial project."""

    order_c = 2.0 if corrected_order else None
    return Project(
        name="Tutorial: Oregonator General Kinetics",
        reactor=ReactorConfig(kind="Batch", nmax=1),
        recipe=Recipe(
            name="oregonator",
            integration=IntegrationControl(t_final=50.0, output_points=240, method="BDF", rtol=1e-8, atol=1e-12),
        ),
        substances=[
            {"name": "A", "alias": "A", "kind": "elemental"},
            {"name": "B", "alias": "BrO3", "kind": "elemental"},
            {"name": "C", "alias": "HBrO2", "kind": "elemental"},
            {"name": "D", "alias": "HOBr", "kind": "elemental"},
            {"name": "E", "alias": "Ce", "kind": "elemental"},
        ],
        general_initial_conditions={
            "A": 0.003,
            "B": 0.1,
            "C": 0.001,
            "D": 0.0,
            "E": 0.05,
        },
        general_kinetic_steps=[
            GeneralKineticStep(
                name="r1",
                reactants=(_p("A"), _p("B")),
                products=(_p("C"), _p("D")),
                forward_parameter="k1",
            ),
            GeneralKineticStep(
                name="r2",
                reactants=(_p("A"), _p("C")),
                products=(_p("D", 2.0),),
                forward_parameter="k2",
            ),
            GeneralKineticStep(
                name="r3",
                reactants=(_p("B"), _p("C")),
                products=(_p("E", 2.0), _p("C", 2.0)),
                forward_parameter="k3",
            ),
            GeneralKineticStep(
                name="r4",
                reactants=(_p("C", order=order_c),),
                products=(_p("B"), _p("D")),
                forward_parameter="k4",
            ),
            GeneralKineticStep(
                name="r5",
                reactants=(_p("E"),),
                products=(_p("A"),),
                forward_parameter="k5",
            ),
        ],
        generic_parameters={
            "k1": 1.3,
            "k2": 2.0e6,
            "k3": 34.0,
            "k4": 3000.0,
            "k5": 0.02,
            "0": 0.0,
            "2": 2.0,
        },
    )


def _p(species: str, stoichiometry: float = 1.0, order: float | None = None) -> GeneralKineticParticipant:
    return GeneralKineticParticipant(species=species, stoichiometry=stoichiometry, order=order)
