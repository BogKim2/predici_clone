# predici_clone

`predici_clone` is an open Python implementation of PREDICI-style polymer-reaction
simulation workflows. It combines a PySide6 desktop application with a Python API for
polymer kinetics, population balances, hybrid Monte Carlo analysis, reactor models,
thermodynamics, parameter fitting, and result export.

The current release is **v2.0.0**. This project is intended for research, education,
and reproducible validation. It is not a drop-in replacement for commercial PREDICI
software or its proprietary file formats.

## Highlights

- Batch, semi-batch, CSTR, cascade, and PFR reactor workflows
- Deterministic, projected/direct Galerkin, and hybrid Monte Carlo simulation
- Polymer molecular-weight distributions, moments, GPC output, and particle-size models
- Controlled-radical, step-growth, crosslinking, copolymer, emulsion, and multiphase models
- Peng-Robinson thermodynamics and PT flash calculations
- Parameter estimation, sensitivity analysis, replay, optimal control, and PID support
- PySide6 GUI plus project/result persistence and automation APIs
- A 39-document headless reproduction suite with HTML, Markdown, JSON, and CSV reports

## Requirements

- Python 3.11 or newer
- Windows is the primary supported desktop and packaging environment
- A graphical desktop session for interactive GUI use

Core dependencies, including NumPy, SciPy, Matplotlib, pandas, PySide6, openpyxl,
and networkx, are installed from `pyproject.toml`.

## Install

```powershell
git clone https://github.com/BogKim2/predici_clone.git
cd predici_clone
python -m pip install -e .
```

For manual builds, install the documentation dependency too:

```powershell
python -m pip install -r manual\requirements.txt
```

## Start the application

After installation, either command starts the desktop application:

```powershell
predici-clone
# or
python -m predici_clone.app.main
```

Run the non-interactive GUI smoke check with:

```powershell
python -m predici_clone.app.main --smoke
```

## Python API quick start

```python
from predici_clone.api import IntegrationControl, Project, ReactorConfig, Recipe
from predici_clone.engine import SimulationEngine

project = Project(
    reactor=ReactorConfig(kind="Batch", nmax=80),
    recipe=Recipe(
        integration=IntegrationControl(t_final=10.0, output_points=50)
    ),
)

result = SimulationEngine(project).run()

print("success:", result.success)
print("Mn:", result.final_moments.mn)
print("Mw:", result.final_moments.mw)
print("PDI:", result.final_moments.pdi)
```

Runnable workflows are available in [`examples/`](examples):

```powershell
python .\examples\tutorial_polyethylene_basic.py
python .\examples\tutorial_oregonator.py
python .\examples\industrial_semibatch_cstr.py
python .\examples\automation_full_workflow.py
```

## Manual reproduction suite

The suite maps 39 source documents to executable, headless scenarios. It can list the
coverage, run a fast subset, or reproduce the complete report set.

```powershell
python -m test_manuals --list
python -m test_manuals --smoke
python -m test_manuals --all
```

To regenerate the checked-in split reports:

```powershell
python -m test_manuals --all --split --output .\test_manual_result
```

The latest published run reports `PASS 39 / FAIL 0 / SKIP 0` and 39/39 PDF coverage.
See the [result index](test_manual_result/README.md) and the
[suite reference](test_manuals/README.md) for filters, output formats, and standalone
per-document runners.

## Build the manual

The maintained Sphinx sources are in [`manual/`](manual). Build them with warnings
treated as errors:

```powershell
sphinx-build -b html -W manual manual\_build\html
Start-Process .\manual\_build\html\index.html
```

Start with the [end-to-end user guide](manual/user_guide.rst), then use the focused
chapters for the [GUI](manual/gui.rst), [project format](manual/projects.rst),
[outputs](manual/outputs.rst), [fitting](manual/fitting.rst), and
[Python API](manual/api.rst).

## Verify a checkout

```powershell
python -m pytest -q
python -m predici_clone.app.main --smoke
sphinx-build -b html -W manual manual\_build\html
```

Release verification records are available in
[`docs/v2_ci_report.md`](docs/v2_ci_report.md) and
[`docs/v2_benchmark_report.md`](docs/v2_benchmark_report.md).

## Windows executable

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm --clean packaging\pyinstaller_predici_clone.spec
.\dist\PrediciClone\PrediciClone.exe --smoke
```

Use `.\scripts\packaging_smoke_test_v2.ps1` for the complete v2 packaging check.
Additional notes are in [`packaging/README.md`](packaging/README.md).

## Repository map

```text
predici_clone/       application and simulation packages
examples/            runnable API workflows
tests/               automated unit and integration tests
test_manuals/        manual-reproduction runner and report generator
test_manual_result/  published 39-document reproduction results
manual/              Sphinx user and developer documentation
docs/                release verification and benchmark reports
packaging/           PyInstaller configuration
```

See [`CHANGELOG.md`](CHANGELOG.md) for release changes and [`plan6.md`](plan6.md) for
the implemented v2 scope.
