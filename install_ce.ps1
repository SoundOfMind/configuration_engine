$ErrorActionPreference = "Stop"

$repositoryPath = $PSScriptRoot
$pythonPath = Join-Path $repositoryPath ".venv\Scripts\python.exe"
$launcherPath = Join-Path $repositoryPath "run_ce.ps1"
$iconPath = Join-Path $repositoryPath "configuration_engine.ico"

if (-not (Test-Path -LiteralPath $pythonPath -PathType Leaf)) {
    Write-Host ""
    Write-Host "Configuration Engine is not installed in the virtual environment." -ForegroundColor Yellow
    Write-Host "Run the installation instructions in the README first." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

if (-not (Test-Path -LiteralPath $launcherPath -PathType Leaf)) {
    Write-Host ""
    Write-Host "Configuration Engine launcher was not found." -ForegroundColor Yellow
    Write-Host "Expected: $launcherPath" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

if (-not (Test-Path -LiteralPath $iconPath -PathType Leaf)) {
    Write-Host ""
    Write-Host "Configuration Engine icon was not found." -ForegroundColor Yellow
    Write-Host "Expected: $iconPath" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

$desktopPath = [Environment]::GetFolderPath("Desktop")

if ([string]::IsNullOrWhiteSpace($desktopPath)) {
    throw "Unable to determine the Windows Desktop location."
}

$shortcutPath = Join-Path $desktopPath "Configuration Engine.lnk"
$powerShellPath = "$env:SystemRoot\System32\WindowsPowerShell\v1.0\powershell.exe"

$wshShell = New-Object -ComObject WScript.Shell
$shortcut = $wshShell.CreateShortcut($shortcutPath)

$shortcut.TargetPath = $powerShellPath
$shortcut.Arguments = "-NoProfile -ExecutionPolicy Bypass -File `"$launcherPath`""
$shortcut.WorkingDirectory = $repositoryPath
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Description = "Start Configuration Engine"

$shortcut.Save()

Write-Host ""
Write-Host "Configuration Engine shortcut installed." -ForegroundColor Green
Write-Host ""
Write-Host "Desktop:    $shortcutPath"
Write-Host "Repository: $repositoryPath"
Write-Host ""
Read-Host "Press Enter to close"