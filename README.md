# predici_clone

PREDICI-style polymerization simulation prototype with a PySide6 desktop interface, reactor models, fitting utilities, scripted outputs, and validation tests.

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

See `plan3.md` and `docs/plan3_progress.md` for the implementation roadmap and current progress.
