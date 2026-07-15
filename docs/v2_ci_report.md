# v2.0 CI Report

Date: 2026-07-15

- `python -m pytest -q`: 215 passed in 25.78 seconds.
- `python -m test_manuals --all`: 39 passed, 0 failed, 0 skipped.
- `sphinx-build -b html -W manual manual/_build/html`: passed with warnings treated as errors.
- `git diff --check`: passed.

- `scripts/packaging_smoke_test_v2.ps1`: passed, including a clean PyInstaller build and packaged `PrediciClone.exe --smoke` run.
- Packaged executable: `dist/PrediciClone/PrediciClone.exe` (41,971,861 bytes).
