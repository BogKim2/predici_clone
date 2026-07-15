$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

python -m pytest -q tests/test_packaging_files.py tests/test_manual_suite.py
sphinx-build -b html -W manual manual/_build/html
pyinstaller --noconfirm --clean packaging/pyinstaller_predici_clone.spec
& "$root/dist/PrediciClone/PrediciClone.exe" --smoke
python -m test_manuals --smoke
