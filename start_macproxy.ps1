#!/usr/bin/env pwsh

<#
.SYNOPSIS
	Windows-compatible script to set up and launch Macproxy Plus

.DESCRIPTION
	This script does the following:
	1. Checks that Python and the venv module are installed.
	2. Creates and/or validates a virtual environment.
	3. Installs required Python packages (from requirements.txt and any enabled extensions).
	4. Launches the proxy server, optionally using a specified port.

.PARAMETER Port
	Specifies the port number for the proxy server.

.EXAMPLE
	.\start_macproxy.ps1 -Port 8080
#>

param (
	[string]$Port
)

function FailAndExit($message) {
	Write-Host "`nERROR: $message"
	Write-Host "Aborting."
	exit 1
}

# Verify Python and venv are installed
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
	FailAndExit "python could not be found.`nInstall Python from https://www.python.org/downloads/"
}

try {
	python -m venv --help | Out-Null
}
catch {
	FailAndExit "venv could not be found. Make sure the Python installation includes the 'venv' module."
}

# Set working directory to script location
Set-Location $PSScriptRoot

$venvPath = Join-Path $PSScriptRoot "venv"
$venvOk = $true

# Test for known broken venv states
if (Test-Path $venvPath) {
	$activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
	if (-not (Test-Path $activateScript)) {
		$venvOk = $false
	}
	else {
		. $activateScript
		try {
			pip list | Out-Null
		}
		catch {
			$venvOk = $false
		}
	}
	if (-not $venvOk) {
		Write-Host "Deleting bad python venv..."
		Remove-Item -Recurse -Force $venvPath
	}
}

# Create the venv if it doesn't exist
if (-not (Test-Path $venvPath)) {
	Write-Host "Creating python venv for Macproxy Plus..."
	python -m venv venv
	Write-Host "Activating venv..."
	. (Join-Path $venvPath "Scripts\Activate.ps1")
	Write-Host "Installing base requirements.txt..."
	pip install wheel | Out-Null
	pip install -r requirements.txt | Out-Null
	try {
		$head = (git rev-parse HEAD)
		Set-Content -Path (Join-Path $PSScriptRoot "current") -Value $head
	}
	catch {
		Write-Host "Warning: Git not found, skipping writing HEAD commit info."
	}
}

. (Join-Path $venvPath "Scripts\Activate.ps1")

# Gather all requirements from enabled extensions
$allRequirements = @()
$enabledExtensions = python -c "import config; print(' '.join(config.ENABLED_EXTENSIONS))"
foreach ($ext in $enabledExtensions.Split()) {
	$reqFile = Join-Path -Path $PSScriptRoot -ChildPath "extensions" | 
			   Join-Path -ChildPath $ext | 
			   Join-Path -ChildPath "requirements.txt"
	if (Test-Path $reqFile) {
		$allRequirements += "-r `"$reqFile`""
	}
}

# Install all requirements at once if there are any
if ($allRequirements.Count -gt 0) {
	Write-Host "Installing requirements for enabled extensions..."
	$pipCommand = "pip install $($allRequirements -join ' ') -q --upgrade"
	Invoke-Expression $pipCommand
}
else {
	Write-Host "No additional requirements for enabled extensions."
}

# Start Macproxy Plus
Write-Host "Starting Macproxy Plus..."
if ($Port) {
	python proxy.py --port $Port
}
else {
	python proxy.py
}