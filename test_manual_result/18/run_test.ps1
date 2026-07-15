param([switch]$NoOpen)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $repoRoot
try {
    python -m test_manuals --pdf 'Predici11_Kinetic_Model.pdf' --output $PSScriptRoot
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}
if (-not $NoOpen) {
    Start-Process (Join-Path $PSScriptRoot 'report.html')
}
