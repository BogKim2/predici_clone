from predici_clone.kinetics.reaction import ReactionKind
from predici_clone.kinetics.reaction_builder import filter_reaction_patterns, reaction_pattern_catalog
from predici_clone.kinetics.step_library import filter_step_definitions, get_step_definition, step_definitions


def test_catalog_contains_exactly_95_unique_step_families():
    definitions = step_definitions()

    assert len(definitions) == 95
    assert len({item.name for item in definitions}) == 95
    assert sum(item.is_pde for item in definitions) == 28
    assert all(item.parameter_slots for item in definitions)


def test_step_flags_and_alias_lookup_cover_polymer_phase_and_pde_steps():
    assert get_step_definition("Propagation").is_polymer
    assert get_step_definition("PhaseExchange").is_phase
    assert get_step_definition("PDE:Nucleation").is_pde
    assert get_step_definition("Transfer(agent)").name == "ChainTransfer"


def test_pattern_finder_exposes_full_catalog_and_legacy_patterns():
    patterns = reaction_pattern_catalog()
    pde_names = {item.name for item in filter_reaction_patterns("nucleation", category="pde")}
    termination = get_step_definition("TerminationDisproportionation")

    assert len(patterns) == 95
    assert "PDE:Nucleation" in pde_names
    assert termination.kind == ReactionKind.TERMINATION_DISPROPORTIONATION
    assert filter_step_definitions("arrhenius", category="growth")
