# Packaging

Initial Windows packaging target uses PyInstaller.

```powershell
python -m pip install pyinstaller
pyinstaller packaging\pyinstaller_predici_clone.spec
```

Pre-build smoke check:

```powershell
python -c "from predici_clone.api.packaging_smoke import inspect_pyinstaller_packaging; report=inspect_pyinstaller_packaging(); print(report.success, report.pyinstaller_available, report.checks)"
```

Smoke checks after build:

1. `dist\PrediciClone\PrediciClone.exe` starts.
2. A sample project can be opened and saved.
3. A Batch simulation runs.
4. Result export writes `manifest.json`, `distribution_history.npz`, `distribution_final.csv`, and `moments.csv`.

Automated executable smoke:

```powershell
.\dist\PrediciClone\PrediciClone.exe --smoke
```

The smoke mode starts the PySide6 application offscreen, runs the default simulation, exports a result bundle to a temporary directory, and exits with code `0` on success.
