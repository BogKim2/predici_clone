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
- M27 script command catalog/template foundation
  - data-driven script function catalog with implemented/stub command markers
  - safe scripted-output evaluator supports string arguments and whitelisted command callables
  - PREDICI-style getters/setters: `getx`, `getco`, `getcoini`, `getconsum`, `getcf`, `getmy`, `gettotalmy`, `getkp`, `setkp`
  - template generator emits boilerplate from selected species/parameters and result slots
  - tests: `tests/test_script_catalog.py`, `tests/test_scripted_outputs.py`
- M28 script-driven reaction modifier foundation
  - parses `k(File)` replacement and `k*File` multiplier forms
  - evaluates modifier scripts through the safe command namespace
  - supports multi-result scripts (`result1`, `result2`, ...) for multi-coefficient reaction steps
  - tests: `tests/test_reaction_modifiers.py`
- M26 chart/reference/GPC weighting core foundation
  - `ChartConfig` for distribution/moment/Monte Carlo chart options
  - GPC `W(log M)` profile calculation (`P(s) * s^2`)
  - reference `.dat`, structured `.npz`, and two-column GPC CSV IO paths
  - `gpc_tail` residual weighting contract
  - tests: `tests/test_chart_reference_io.py`
- M29/M32 run-control engine foundation
  - `SimulationEngine.run_to_time(t)` API
  - `SimulationEngine.single_step()` API
  - `SimulationResult.actual_values_history()` plus result metadata for step/time/stepsize/n_variables
  - deterministic final-time resume check against full run
  - tests: `tests/test_run_control.py`

## Still Incomplete

- M23 component administration GUI polish
- M24 PatternFinder-style GUI integration and richer template catalog
- M25 recipe consistency GUI workflow
- M26 chart administration GUI and components information board
- M27 GUI catalog rendering and additional command implementations
- M28 GUI integration and modifier-to-engine execution hooks
- M29 GUI debugger/multi-script panes and edit-in-place workflow
- M32 GUI simulation-mode controls and moments backend
- M31 tutorial manual expansion and full regression suite
