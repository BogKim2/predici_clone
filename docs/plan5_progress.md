# plan5 Implementation Progress

This file tracks implementation evidence against `plan5.md`.

## Implemented With Tests

- M33 GUI modernization foundation
  - reusable `EditableTableWidget` for GUI tables
  - `SpeciesIconProvider` and explicit visual color tokens
  - `MainWindow` table instances use `EditableTableWidget`
  - tests: `tests/test_gui_modernization.py`
- M34 reactor expansion evidence
  - PFR/cascade/heat balance modules and engine integration already present
  - cascade-to-PFR benchmark runner added
  - tests: `tests/test_reactors.py`, `tests/test_engine_project.py`, `tests/test_galerkin_backend.py`, `tests/test_plan5_benchmarks.py`
- M35 parameter estimation evidence
  - local least-squares and dual-annealing global search are implemented
  - synthetic FRP recovery benchmark added
  - tests: `tests/test_parameter_estimation.py`, `tests/test_global_search.py`, `tests/test_plan5_benchmarks.py`
- M36 sensitivity and shooting evidence
  - sigma-point and Monte Carlo sensitivity are implemented
  - shooting control is routed through detailed iteration fitting
  - tests: `tests/test_sensitivity.py`, `tests/test_shooting.py`
- M37 copolymer 2D distribution foundation
  - `TensorDistribution2D` tensor-product distribution
  - terminal-model Mayo-Lewis composition helper
  - single-composition marginal equals the 1D chain distribution
  - tests: `tests/test_copolymer_2d.py`, `tests/test_plan5_benchmarks.py`
- M38 automation API/export completion
  - `run_automation_workflow()` covers model -> recipe -> simulation -> query
  - `export_result_npz()` writes time/state/distribution arrays
  - public command dispatcher exposes `RunAutomationWorkflow` and `ExportResultNPZ`
  - example: `examples/automation_full_workflow.py`
  - tests: `tests/test_automation_api.py`, `tests/test_interoperability.py`
- M39 packaging/release smoke
  - PyInstaller spec and README already present
  - `scripts/packaging_smoke_test.ps1` added for preflight/build smoke
  - tests: `tests/test_packaging_files.py`
- M40 regression freeze artifacts
  - benchmark runner: `predici_clone/validation/benchmark_runner.py`
  - reports: `docs/v1_benchmark_report.md`, `docs/v1_ci_report.md`
  - release notes: `CHANGELOG.md`

## Still Incomplete

- None.
