# Creates the McCurdy folder layout and installs the toolkit's Python packages.
# Run in PowerShell from the toolkit folder:  powershell -ExecutionPolicy Bypass -File scripts\setup_windows.ps1
param([string]$Root = "D:\McCurdy")

$ErrorActionPreference = "Stop"
foreach ($d in "Jobs", "Prospects", "Brand", "Admin", "Toolkit") {
    New-Item -ItemType Directory -Force -Path (Join-Path $Root $d) | Out-Null
}
Write-Host "Folders ready under $Root"

if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
    Write-Warning "Python not found. Install Python 3.12+ from python.org (tick 'Add to PATH'), then run this again."
    exit 1
}

$toolkit = Split-Path -Parent $PSScriptRoot
Push-Location $toolkit
if (-not (Test-Path ".venv")) { py -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip | Out-Null
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt
& .\.venv\Scripts\python.exe -m mccurdy proposal examples\job_example.yaml
Pop-Location

Write-Host ""
Write-Host "Done. Next: open config\company.yaml and replace every REPLACE_ME with your real details and prices."
