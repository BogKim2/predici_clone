param(
    [switch]$Build
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$report = python -c "from predici_clone.api.packaging_smoke import inspect_pyinstaller_packaging; r=inspect_pyinstaller_packaging(); print(r.success); print(r.pyinstaller_available); print(r.checks)"
Write-Output $report

if ($Build) {
    pyinstaller --noconfirm packaging\pyinstaller_predici_clone.spec
    if (-not (Test-Path dist\PrediciClone)) {
        throw "dist\PrediciClone was not created"
    }
}
