$ErrorActionPreference = "Stop"

Write-Host "RedPA AI v3.0.0 - Build Release Archive" -ForegroundColor Cyan

python .\scripts\release\build_v3_archive.py

if ($LASTEXITCODE -ne 0) {
    throw "Release archive generation failed."
}

Write-Host ""
Get-Item .\dist\redpa-ai-v3.0.0.zip
Get-Content .\dist\redpa-ai-v3.0.0.sha256
