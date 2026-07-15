param([switch]$NoOpen)
$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
Push-Location $repoRoot
try {
    python -m test_manuals --pdf 'Predici Version_11_16_1_20170717.pdf' --output $PSScriptRoot
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} finally {
    Pop-Location
}
if (-not $NoOpen) {
    Start-Process (Join-Path $PSScriptRoot 'report.html')
}
