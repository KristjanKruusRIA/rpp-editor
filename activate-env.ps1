# Virtual Environment Activation Script
# This script activates the Python virtual environment for the rpp-editor project

# For PowerShell (Windows)
& "$(Join-Path $PSScriptRoot '.venv' 'Scripts' 'Activate.ps1')"

Write-Host "RPP Editor virtual environment activated!" -ForegroundColor Green
Write-Host "Python: $((Get-Command python).Source)" -ForegroundColor Cyan
Write-Host "Pip: $((Get-Command pip).Source)" -ForegroundColor Cyan

# Verify pytest is available
try {
    $pytestVersion = python -c "import pytest; print(pytest.__version__)"
    Write-Host "pytest version: $pytestVersion" -ForegroundColor Green
} catch {
    Write-Host "Warning: pytest not found" -ForegroundColor Yellow
}

# Verify rpp_editor package is available
try {
    python -c "import rpp_editor; print('rpp_editor package: OK')" 2>$null
    Write-Host "rpp_editor package: OK" -ForegroundColor Green
} catch {
    Write-Host "Warning: rpp_editor package not found" -ForegroundColor Yellow
}