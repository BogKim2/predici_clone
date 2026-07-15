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

## Still Incomplete

- M23 component administration GUI/schema polish
- M24 PatternFinder-style reaction builder
- M25 recipe consistency workflow
- M26 chart administration/reference data
- M27 tutorial script command aliases
- M28 script-driven reaction modifiers
- M29 script debugger and run-to-time control
- M31 tutorial manual expansion and full regression suite
