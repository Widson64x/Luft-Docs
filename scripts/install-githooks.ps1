$ErrorActionPreference = "Stop"

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")

git -C $repoRoot config core.hooksPath .githooks

Write-Host "Git hooks configurados com sucesso em .githooks"