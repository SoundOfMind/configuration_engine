Set-Location $PSScriptRoot

& ".\.venv\Scripts\python.exe" -m configuration_engine.tui

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "Configuration Engine could not start." -ForegroundColor Yellow
    Write-Host "Another instance of Configuration Engine may already be running." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to close"
}

exit $LASTEXITCODE