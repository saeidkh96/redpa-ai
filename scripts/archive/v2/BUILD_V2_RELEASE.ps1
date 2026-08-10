$ErrorActionPreference = "Stop"

$version = "v2.0.0"
$dist = ".\dist"
$archive = Join-Path $dist "redpa-ai-$version.zip"

New-Item -ItemType Directory -Force -Path $dist | Out-Null

git rev-parse --is-inside-work-tree 2>$null | Out-Null
if ($LASTEXITCODE -ne 0) { throw "A Git working tree is required." }

if (Test-Path $archive) { Remove-Item $archive -Force }

git archive --format=zip --output=$archive HEAD
if ($LASTEXITCODE -ne 0) { throw "git archive failed." }

$hash = (Get-FileHash $archive -Algorithm SHA256).Hash
"$hash  redpa-ai-$version.zip" | Set-Content "$archive.sha256" -Encoding ASCII

Write-Host "Release archive: $archive" -ForegroundColor Green
Write-Host "SHA256: $hash" -ForegroundColor Green
Write-Host ""
Write-Host "git archive contains committed files only." -ForegroundColor Yellow
