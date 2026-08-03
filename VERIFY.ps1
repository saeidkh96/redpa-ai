$ErrorActionPreference = "Stop"

python scripts\install_phase_9_6.py
python scripts\final_release_check.py
python scripts\create_release_archive.py

Write-Host ""
Write-Host "Health:"
Invoke-RestMethod http://localhost:8000/api/v1/platform/health

Write-Host ""
Write-Host "Release archive:"
Get-Item .\dist\redpa-ai-v1.0.0.zip
