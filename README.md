# predici_clone

PREDICI-style polymerization simulation suite with a PySide6 desktop interface, deterministic and hybrid Monte Carlo kinetics, population balances, emulsion and multiphase models, Peng-Robinson thermodynamics, parameter estimation, replay, and interoperability tools.

## Setup

```powershell
python -m pip install -e .
```

## Tests

```powershell
python -m pytest -q
```

## Run GUI

```powershell
python -m predici_clone.app.main
```

## Build Windows Executable

```powershell
python -m pip install pyinstaller
pyinstaller --noconfirm packaging\pyinstaller_predici_clone.spec
.\dist\PrediciClone\PrediciClone.exe --smoke
```

## Manual

Sphinx source files live under `manual`.

```powershell
python -m pip install -r manual\requirements.txt
sphinx-build -b html manual manual\_build\html
```

Open `manual\_build\html\index.html` after the build.

See `plan3.md` and `docs/plan3_progress.md` for the implementation roadmap and current progress.

## Manual Reproduction Suite

The headless suite maps 39 feature-bearing source PDFs to executable scenarios:

```powershell
python -m test_manuals --list
python -m test_manuals --smoke
python -m test_manuals --all
```

See `plan6.md`, `docs/v2_benchmark_report.md`, and `docs/v2_ci_report.md` for the v2.0 scope and release evidence.
