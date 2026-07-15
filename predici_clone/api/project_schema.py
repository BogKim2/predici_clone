from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from predici_clone.kinetics.reaction import RateLaw, ReactionKind, ReactionStep


ReactorKind = Literal["Batch", "Semi-batch", "CSTR", "Cascade", "PFR"]


@dataclass(frozen=True)
class FRPParameters:
    kp: float = 0.08
    kt: float = 0.05
    kd: float = 0.02
    initiator_efficiency: float = 0.6


@dataclass(frozen=True)
class InitialConditions:
    monomer: float = 2.0
    initiator: float = 0.15
    radicals: float = 0.0


@dataclass(frozen=True)
class FeedStream:
    monomer: float = 2.0
    initiator: float = 0.15
    radicals: float = 0.0
    rate: float = 0.06


@dataclass(frozen=True)
class ProfilePoint:
    time: float
    value: float


@dataclass(frozen=True)
class IntegrationControl:
    t_final: float = 30.0
    output_points: int = 80
    method: str = "BDF"
    rtol: float = 1e-7
    atol: float = 1e-10
    backend: str = "discrete"
    galerkin_cells: int = 8
    galerkin_degree: int = 2


@dataclass(frozen=True)
class ReactorConfig:
    kind: ReactorKind = "Batch"
    nmax: int = 120
    volume: float = 1.0
    residence_time: float = 8.0
    stages: int = 4
    axial_cells: int = 12


@dataclass(frozen=True)
class OutputConfig:
    distribution_mode: str = "weight"
    log_axis: bool = False
    gpc_convolution: bool = False
    enabled_generic_outputs: tuple[str, ...] = ("Mn", "Mw", "PDI", "conversion")
    scripted_outputs: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class HeatBalanceConfig:
    enabled: bool = False
    use_heat_exchanger: bool = False
    heat_transfer: float = 0.0
    area: float = 0.0
    heat_capacity: float = 0.0
    mass_flow: float = 0.0
    mass_holdup: float = 0.0
    initial_feed_temp: float = 298.15
    coolant_temperature: float = 298.15
    additional_heat: float = 0.0
    counter_current: bool = False


@dataclass(frozen=True)
class GeneralKineticParticipant:
    species: str
    stoichiometry: float = 1.0
    order: float | None = None


@dataclass(frozen=True)
class GeneralKineticStep:
    name: str
    reactants: tuple[GeneralKineticParticipant, ...]
    products: tuple[GeneralKineticParticipant, ...]
    forward_parameter: str
    backward_parameter: str = "0"
    enabled: bool = True
    equilibrium: bool = False


@dataclass(frozen=True)
class Substance:
    name: str
    alias: str = ""
    kind: str = "species"
    molecular_weight: float = 0.0
    density: float = 0.0
    is_monomer: bool = False
    groups: tuple[str, ...] = ()


@dataclass(frozen=True)
class PolymerSpecies:
    name: str
    alias: str = ""
    base_monomer: str = ""
    active: bool = False
    dead: bool = True
    molecular_weight: float = 0.0
    density: float = 0.0
    groups: tuple[str, ...] = ()


@dataclass(frozen=True)
class Parameter:
    name: str
    value: float = 0.0
    unit: str = ""
    kind: str = "scalar"
    pre_exponential: float | None = None
    activation_energy: float | None = None


@dataclass(frozen=True)
class Recipe:
    name: str = "default"
    unit_system: str = "SI"
    initial: InitialConditions = field(default_factory=InitialConditions)
    feed: FeedStream = field(default_factory=FeedStream)
    feed_tanks: list[FeedStream] = field(default_factory=list)
    polymer_feed: list[dict[str, Any]] = field(default_factory=list)
    integration: IntegrationControl = field(default_factory=IntegrationControl)
    pre_schedule: list[dict[str, Any]] = field(default_factory=list)
    temperature_profile: list[ProfilePoint] = field(default_factory=list)
    pressure_profile: list[ProfilePoint] = field(default_factory=list)
    shooting_control: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class Project:
    schema_version: int = 1
    name: str = "PREDICI Clone Project"
    reactor: ReactorConfig = field(default_factory=ReactorConfig)
    kinetics: FRPParameters = field(default_factory=FRPParameters)
    recipe: Recipe = field(default_factory=Recipe)
    outputs: OutputConfig = field(default_factory=OutputConfig)
    heat_balance: HeatBalanceConfig = field(default_factory=HeatBalanceConfig)
    substances: list[dict[str, Any]] = field(default_factory=list)
    polymers: list[dict[str, Any]] = field(default_factory=list)
    reaction_steps: list[ReactionStep] = field(default_factory=list)
    general_kinetic_steps: list[GeneralKineticStep] = field(default_factory=list)
    general_initial_conditions: dict[str, float] = field(default_factory=dict)
    generic_parameters: dict[str, float] = field(default_factory=dict)
    parameters: list[Parameter] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Project":
        recipe_data = data.get("recipe", {})
        recipe = Recipe(
            name=recipe_data.get("name", "default"),
            unit_system=recipe_data.get("unit_system", "SI"),
            initial=InitialConditions(**recipe_data.get("initial", {})),
            feed=FeedStream(**recipe_data.get("feed", {})),
            feed_tanks=[_feed_stream_from_dict(item) for item in recipe_data.get("feed_tanks", [])],
            polymer_feed=recipe_data.get("polymer_feed", []),
            integration=IntegrationControl(**recipe_data.get("integration", {})),
            pre_schedule=recipe_data.get("pre_schedule", []),
            temperature_profile=[_profile_point_from_dict(item) for item in recipe_data.get("temperature_profile", [])],
            pressure_profile=[_profile_point_from_dict(item) for item in recipe_data.get("pressure_profile", [])],
            shooting_control=recipe_data.get("shooting_control", {}),
        )
        return cls(
            schema_version=data.get("schema_version", 1),
            name=data.get("name", "PREDICI Clone Project"),
            reactor=ReactorConfig(**data.get("reactor", {})),
            kinetics=FRPParameters(**data.get("kinetics", {})),
            recipe=recipe,
            outputs=OutputConfig(**data.get("outputs", {})),
            heat_balance=HeatBalanceConfig(**data.get("heat_balance", {})),
            substances=data.get("substances", []),
            polymers=data.get("polymers", []),
            reaction_steps=[_reaction_step_from_dict(item) for item in data.get("reaction_steps", [])],
            general_kinetic_steps=[
                _general_kinetic_step_from_dict(item)
                for item in data.get("general_kinetic_steps", [])
            ],
            general_initial_conditions={
                str(name): float(value)
                for name, value in data.get("general_initial_conditions", {}).items()
            },
            generic_parameters=data.get("generic_parameters", {}),
            parameters=[_parameter_from_dict(item) for item in data.get("parameters", [])],
        )


def sample_project(kind: ReactorKind = "Batch") -> Project:
    return Project(reactor=ReactorConfig(kind=kind))


def _reaction_step_from_dict(data: dict[str, Any] | ReactionStep) -> ReactionStep:
    if isinstance(data, ReactionStep):
        return data
    rate_data = data.get("rate_law", {})
    return ReactionStep(
        name=data.get("name", "reaction"),
        kind=ReactionKind(data.get("kind", ReactionKind.PROPAGATION)),
        reactants=tuple(data.get("reactants", ())),
        products=tuple(data.get("products", ())),
        rate_law=RateLaw(
            expression=rate_data.get("expression", ""),
            parameters=tuple(rate_data.get("parameters", ())),
        ),
        enabled=data.get("enabled", True),
        site=data.get("site", "default"),
        reactor_scope=data.get("reactor_scope", "all"),
    )


def _profile_point_from_dict(data: dict[str, Any] | ProfilePoint) -> ProfilePoint:
    if isinstance(data, ProfilePoint):
        return data
    return ProfilePoint(time=float(data.get("time", 0.0)), value=float(data.get("value", 0.0)))


def _feed_stream_from_dict(data: dict[str, Any] | FeedStream) -> FeedStream:
    if isinstance(data, FeedStream):
        return data
    return FeedStream(
        monomer=float(data.get("monomer", 0.0)),
        initiator=float(data.get("initiator", 0.0)),
        radicals=float(data.get("radicals", 0.0)),
        rate=float(data.get("rate", 0.0)),
    )


def _general_kinetic_participant_from_dict(data: dict[str, Any] | GeneralKineticParticipant) -> GeneralKineticParticipant:
    if isinstance(data, GeneralKineticParticipant):
        return data
    order = data.get("order", None)
    return GeneralKineticParticipant(
        species=str(data.get("species", "")),
        stoichiometry=float(data.get("stoichiometry", 1.0)),
        order=None if order is None else float(order),
    )


def _general_kinetic_step_from_dict(data: dict[str, Any] | GeneralKineticStep) -> GeneralKineticStep:
    if isinstance(data, GeneralKineticStep):
        return data
    return GeneralKineticStep(
        name=str(data.get("name", "general_step")),
        reactants=tuple(_general_kinetic_participant_from_dict(item) for item in data.get("reactants", ())),
        products=tuple(_general_kinetic_participant_from_dict(item) for item in data.get("products", ())),
        forward_parameter=str(data.get("forward_parameter", "0")),
        backward_parameter=str(data.get("backward_parameter", "0")),
        enabled=bool(data.get("enabled", True)),
        equilibrium=bool(data.get("equilibrium", False)),
    )


def _parameter_from_dict(data: dict[str, Any] | Parameter) -> Parameter:
    if isinstance(data, Parameter):
        return data
    return Parameter(
        name=str(data.get("name", "")),
        value=float(data.get("value", 0.0)),
        unit=str(data.get("unit", "")),
        kind=str(data.get("kind", "scalar")),
        pre_exponential=_optional_float(data.get("pre_exponential")),
        activation_energy=_optional_float(data.get("activation_energy")),
    )


def substance_to_dict(substance: Substance | dict[str, Any]) -> dict[str, Any]:
    if isinstance(substance, Substance):
        return asdict(substance)
    return dict(substance)


def polymer_species_to_dict(polymer: PolymerSpecies | dict[str, Any]) -> dict[str, Any]:
    if isinstance(polymer, PolymerSpecies):
        return asdict(polymer)
    return dict(polymer)


def _optional_float(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)
