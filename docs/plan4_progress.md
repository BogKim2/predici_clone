# plan4 Implementation Progress

This file tracks implementation evidence against `plan4.md`.

## Implemented With Tests

- M22 tutorial project templates foundation
  - `predici_clone/validation/tutorial_projects.py`
  - `polyethylene_basic_project()`
  - `oregonator_kinetics_project(corrected_order=...)`
  - examples: `examples/tutorial_polyethylene_basic.py`, `examples/tutorial_oregonator.py`
  - tests: `tests/test_tutorial_projects.py`
- M30 general kinetic model support foundation
  - `GeneralKineticParticipant`
  - `GeneralKineticStep`
  - `Project.general_kinetic_steps`
  - `Project.general_initial_conditions`
  - `SimulationEngine` general concentration ODE path
  - arbitrary reaction order independent of stoichiometric coefficient
  - concentration history and final concentration metadata
  - callback step/progress events for general kinetics
  - tests: `tests/test_tutorial_projects.py`
- M23 component administration schema/API foundation
  - `Substance`, `PolymerSpecies`, `Parameter`
  - `Project.parameters` registry with `generic_parameters` compatibility
  - component add/upsert helpers, auto declaration, numeric-constant parameters
  - reference lookup for polymer reaction steps and general kinetic steps
  - tests: `tests/test_component_admin.py`
- M24 PatternFinder-style reaction builder service foundation
  - searchable reaction pattern catalog
  - polymer reaction step builder with auto-declared species and parameters
  - general kinetic step builder with independent stoichiometry and order
  - tests: `tests/test_reaction_builder.py`
- M25 recipe consistency service foundation
  - seven recipe input modes normalize to mass/mole/concentration tables
  - `Set concentration consistent` density rule
  - `Set rest` remainder fill for mass and mole parts
  - feed tank schema carries feed type, profile, script-control flags, and switch time
  - tests: `tests/test_recipe_consistency.py`

## Still Incomplete

- M23 component administration GUI polish
- M24 PatternFinder-style GUI integration and richer template catalog
- M25 recipe consistency GUI workflow
- M26 chart administration/reference data
- M27 tutorial script command aliases
- M28 script-driven reaction modifiers
- M29 script debugger and run-to-time control
- M31 tutorial manual expansion and full regression suite
