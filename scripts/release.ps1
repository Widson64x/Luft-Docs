$ErrorActionPreference = "Stop"

param(
    [switch]$Push
)

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Set-Location $repoRoot

function Obter-PythonExecutavel {
    $candidatos = @(
        ".\.LUFTDOCS_PACKAGES\Scripts\python.exe",
        ".\.venv\Scripts\python.exe"
    )

    foreach ($candidato in $candidatos) {
        if (Test-Path $candidato) {
            return (Resolve-Path $candidato).Path
        }
    }

    return "python"
}

$python = Obter-PythonExecutavel

$outputFile = New-TemporaryFile

try {
    & $python .\scripts\prepare_release.py --github-output $outputFile

    $releaseMetadata = @{}
    foreach ($linha in Get-Content $outputFile) {
        if ($linha -match '^(?<key>[^=]+)=(?<value>.*)$') {
            $releaseMetadata[$matches['key']] = $matches['value']
        }
    }
} finally {
    if (Test-Path $outputFile) {
        Remove-Item $outputFile -Force
    }
}

if ($releaseMetadata['created'] -ne 'true') {
    Write-Host "Sem novos commits para gerar release."
    return
}

$version = $releaseMetadata['version']

if (-not $version) {
    throw "Nao foi possivel determinar a versao atual do monorepo."
}

if ($version -notmatch '^\d+\.\d+\.\d+$') {
    throw "Versao invalida em _version.py: $version"
}

$tag = "v$version"

if (Test-Path dist) {
    Remove-Item -Recurse -Force dist
}

New-Item -ItemType Directory -Path dist | Out-Null

& $python -m pip install --upgrade pip
& $python -m pip install -r requirements.txt
& $python -m pip install -r .\LuftDocs_API\requirements.txt
& $python -m compileall _version.py scripts Luft-Docs LuftDocs_API
& $python -m py_compile .\Luft-Docs\App.py .\Luft-Docs\Wsgi.py .\LuftDocs_API\Wsgi.py .\LuftDocs_API\App\Main.py

$bundlePath = Join-Path (Resolve-Path .\dist) "luftdocs-$tag.zip"
Compress-Archive -Path @(
    ".\_version.py",
    ".\requirements.txt",
    ".\scripts",
    ".\Luft-Docs",
    ".\LuftDocs_API",
    ".\.github",
    ".\.githooks"
) -DestinationPath $bundlePath -Force

$tagExiste = git tag --list $tag
if ($tagExiste) {
    throw "A tag $tag ja existe. Ajuste a versao antes de prosseguir."
}

git add _version.py CHANGELOG.md
git commit -m "build(release): $tag [skip ci]"

git tag -a $tag -m "build(release): $tag"

if ($Push) {
    git push origin HEAD --follow-tags
    Write-Host "Release $tag publicada no GitHub."
} else {
    Write-Host "Release validada, bundle gerado e tag criada localmente: $tag"
    Write-Host "Para publicar, execute: powershell -ExecutionPolicy Bypass -File .\scripts\release.ps1 -Push"
}