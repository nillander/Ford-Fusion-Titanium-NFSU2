#Requires -Version 5.1
<#
.SYNOPSIS
  Cria a release GitHub vX.Y e remove releases/tags anteriores.

.EXAMPLE
  .\publish-release.ps1 -Version 1.5 -Title "v1.5 — descrição" -Push
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidatePattern('^\d+\.\d+(\.\d+)?$')]
    [string] $Version,

    [Parameter(Mandatory = $true)]
    [string] $Title,

    [switch] $Push,

    [switch] $SkipPush,

    [string] $GhPath,

    [string] $RepoRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Resolve-GhExe {
    param([string] $ExplicitPath)

    if ($ExplicitPath) {
        if (-not (Test-Path -LiteralPath $ExplicitPath)) {
            throw "gh.exe não encontrado em: $ExplicitPath"
        }
        return (Resolve-Path -LiteralPath $ExplicitPath).Path
    }

    $fromPath = Get-Command gh -ErrorAction SilentlyContinue
    if ($fromPath) {
        return $fromPath.Source
    }

    $portable = Get-ChildItem -Path (Join-Path $env:TEMP 'gh-cli') -Recurse -Filter 'gh.exe' -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($portable) {
        return $portable.FullName
    }

    Write-Host 'gh não encontrado; baixando portátil...'
    $ghDir = Join-Path $env:TEMP 'gh-cli'
    New-Item -ItemType Directory -Force -Path $ghDir | Out-Null
    $zipPath = Join-Path $ghDir 'gh.zip'
    $latest = Invoke-RestMethod -Uri 'https://api.github.com/repos/cli/cli/releases/latest'
    $asset = $latest.assets | Where-Object { $_.name -match 'windows_amd64\.zip$' } | Select-Object -First 1
    if (-not $asset) {
        throw 'Asset windows_amd64.zip não encontrado na release do cli/cli.'
    }
    Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath
    Expand-Archive -Path $zipPath -DestinationPath $ghDir -Force
    $installed = Get-ChildItem -Path $ghDir -Recurse -Filter 'gh.exe' | Select-Object -First 1
    if (-not $installed) {
        throw 'Falha ao extrair gh.exe'
    }
    return $installed.FullName
}

if (-not $RepoRoot) {
    # scripts -> publish-release -> skills -> .cursor -> repo root
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
}

Set-Location -LiteralPath $RepoRoot

$tag = "v$Version"
$releaseDir = Join-Path $RepoRoot "local\release-$tag"
$notesFile = Join-Path $RepoRoot "release\notes-$tag.md"

$requiredAssets = @(
    'Fusion2018_AWD_NFSU2.zip'
    'Fusion2012_FWD_NFSU2.zip'
    'instalar.bat'
    'globalb_patch.ps1'
    'SHA256SUMS.txt'
    'SHA256SUMS-conteudo.txt'
)

if (-not (Test-Path -LiteralPath $releaseDir)) {
    throw "Pasta de artefatos ausente: $releaseDir"
}
if (-not (Test-Path -LiteralPath $notesFile)) {
    throw "Notes ausente: $notesFile"
}

$assetPaths = foreach ($assetName in $requiredAssets) {
    $assetPath = Join-Path $releaseDir $assetName
    if (-not (Test-Path -LiteralPath $assetPath)) {
        throw "Artefato ausente: $assetPath"
    }
    $assetPath
}

$gh = Resolve-GhExe -ExplicitPath $GhPath
Write-Host "Usando gh: $gh"
& $gh auth status
if ($LASTEXITCODE -ne 0) {
    throw 'gh não autenticado. Rode: gh auth login'
}

if ($Push -and -not $SkipPush) {
    Write-Host 'Push da branch atual...'
    git push -u origin HEAD
    if ($LASTEXITCODE -ne 0) {
        throw 'git push falhou; release não criada.'
    }
}

$existing = & $gh release list --limit 100
if ($LASTEXITCODE -ne 0) {
    throw 'Falha ao listar releases.'
}

$existingTags = @()
if ($existing) {
    foreach ($line in ($existing -split "`n")) {
        if ([string]::IsNullOrWhiteSpace($line)) { continue }
        # Colunas: title TAB status TAB tag TAB date
        $columns = $line -split "`t"
        if ($columns.Count -ge 3) {
            $existingTags += $columns[2].Trim()
        }
    }
}

if ($existingTags -contains $tag) {
    throw "Release/tag $tag já existe. Apague-a antes ou use outra versão."
}

Write-Host "Criando release $tag ..."
& $gh release create $tag @assetPaths `
    --title $Title `
    --notes-file $notesFile `
    --latest
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao criar release $tag"
}

$tagsToDelete = $existingTags | Where-Object { $_ -and $_ -ne $tag } | Select-Object -Unique
foreach ($oldTag in $tagsToDelete) {
    Write-Host "Removendo release/tag $oldTag ..."
    & $gh release delete $oldTag --cleanup-tag -y
    if ($LASTEXITCODE -ne 0) {
        throw "Falha ao remover $oldTag"
    }
}

Write-Host ''
Write-Host 'Releases restantes:'
& $gh release list --limit 10
$repoName = & $gh repo view --json nameWithOwner -q .nameWithOwner
Write-Host ''
Write-Host "OK: https://github.com/$repoName/releases/tag/$tag"
