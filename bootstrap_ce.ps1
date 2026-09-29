$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "Configuration Engine Installer" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$gitCommand = Get-Command git -ErrorAction SilentlyContinue

if ($null -eq $gitCommand) {
    Write-Host "Git was not found." -ForegroundColor Yellow
    Write-Host "Install Git for Windows and run this installer again." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host "Git:    $($gitCommand.Source)" -ForegroundColor Green

$pythonCommand = Get-Command python -ErrorAction SilentlyContinue

if ($null -eq $pythonCommand) {
    Write-Host "Python was not found." -ForegroundColor Yellow
    Write-Host "Install Python 3.14 or newer and run this installer again." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

$pythonVersionOutput = & $pythonCommand.Source --version 2>&1

if ($LASTEXITCODE -ne 0) {
    Write-Host "Unable to determine the Python version." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host "Python: $pythonVersionOutput" -ForegroundColor Green

$versionText = $pythonVersionOutput -replace "[^0-9.]", ""
$versionParts = $versionText.Split(".")

if ($versionParts.Count -lt 2) {
    Write-Host "Unable to determine the Python version." -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

$pythonMajor = [int]$versionParts[0]
$pythonMinor = [int]$versionParts[1]

if (($pythonMajor -lt 3) -or (($pythonMajor -eq 3) -and ($pythonMinor -lt 14))) {
    Write-Host "Configuration Engine requires Python 3.14 or newer." -ForegroundColor Yellow
    Write-Host "Installed version: $pythonVersionOutput" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to close"
    exit 1
}

Write-Host ""
Write-Host "Prerequisite check passed." -ForegroundColor Green
Write-Host ""

$installParent = Read-Host "Enter the parent directory for Configuration Engine"

if ([string]::IsNullOrWhiteSpace($installParent)) {
    throw "An installation directory is required."
}

$installParent = [Environment]::ExpandEnvironmentVariables($installParent)
$installParent = [System.IO.Path]::GetFullPath($installParent)

Write-Host ""
Write-Host "Installation parent:"
Write-Host "  $installParent"
Write-Host ""

if (-not (Test-Path -LiteralPath $installParent)) {
    Write-Host "Directory does not exist. Creating it..."
    New-Item -ItemType Directory -Path $installParent -Force | Out-Null
}

if (-not (Test-Path -LiteralPath $installParent -PathType Container)) {
    throw "The installation path is not a directory: $installParent"
}

$repositoryPath = Join-Path $installParent "configuration_engine"

if (Test-Path -LiteralPath $repositoryPath) {
    throw "The target directory already exists: $repositoryPath"
}

Write-Host "Target repository:"
Write-Host "  $repositoryPath"
Write-Host ""
Write-Host "Installation location is ready."

Write-Host ""
Write-Host "Cloning Configuration Engine..."
git clone https://github.com/SoundOfMind/configuration_engine.git $repositoryPath

if ($LASTEXITCODE -ne 0) {
    throw "Failed to clone the Configuration Engine repository."
}

Set-Location $repositoryPath

Write-Host ""
Write-Host "Creating Python virtual environment..."
& $pythonCommand.Source -m venv .venv

if ($LASTEXITCODE -ne 0) {
    throw "Failed to create the Python virtual environment."
}

Write-Host "Virtual environment created."

Write-Host ""
Write-Host "Installing Configuration Engine..."
& ".\.venv\Scripts\python.exe" -m pip install -e "."

if ($LASTEXITCODE -ne 0) {
    throw "Failed to install Configuration Engine."
}

Write-Host ""
Write-Host "Configuration Engine installed successfully." -ForegroundColor Green
Write-Host ""

& ".\install_ce.ps1"

if ($LASTEXITCODE -ne 0) {
    throw "Failed to create the Configuration Engine Desktop shortcut."
}