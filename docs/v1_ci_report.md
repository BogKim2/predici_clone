# v1.0 CI Report

Verified local gates:

- `pytest -q` -> 185 passed
- `python -m compileall -q predici_clone tests examples` -> passed
- `sphinx-build -W -b html manual manual/_build/html` -> passed
- `python -c "from predici_clone.api.packaging_smoke import inspect_pyinstaller_packaging; r=inspect_pyinstaller_packaging(); assert r.success"` -> passed
- `powershell -ExecutionPolicy Bypass -File scripts/packaging_smoke_test.ps1 -Build` -> passed
- `dist/PrediciClone/PrediciClone.exe --smoke` -> passed

Release tag gate:

- `v1.0.0` is created after the implementing commit is pushed.
