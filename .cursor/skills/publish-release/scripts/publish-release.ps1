#Requires -Version 5.1
<#
.SYNOPSIS
  Calcula a próxima versão, usa o título do último commit, cria a release e remove as anteriores.

.EXAMPLE
  .\publish-release.ps1 -Push
#>
[CmdletBinding()]
param(
    [ValidatePattern('^\d+\.\d+(\.\d+)?$')]
    [string] $Version,

    [string] $Title,

    [switch] $Push,

    [switch] $SkipPush,

    [string] $GhPath,

    [string] $RepoRoot
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$script:RequiredAssets = @(
    'Fusion2018_AWD_NFSU2.zip'
    'Fusion2012_FWD_NFSU2.zip'
    'instalar.bat'
    'globalb_patch.ps1'
    'SHA256SUMS.txt'
    'SHA256SUMS-conteudo.txt'
)

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

function Test-ReleasePackageComplete {
    param(
        [string] $ReleaseDir,
        [string] $NotesFile
    )

    if (-not (Test-Path -LiteralPath $ReleaseDir)) { return $false }
    if (-not (Test-Path -LiteralPath $NotesFile)) { return $false }
    foreach ($assetName in $script:RequiredAssets) {
        if (-not (Test-Path -LiteralPath (Join-Path $ReleaseDir $assetName))) {
            return $false
        }
    }
    return $true
}

function Get-ExistingReleaseTags {
    param([string] $GhExe)

    $existing = & $GhExe release list --limit 100
    if ($LASTEXITCODE -ne 0) {
        throw 'Falha ao listar releases.'
    }

    $tags = @()
    if ($existing) {
        foreach ($line in ($existing -split "`n")) {
            if ([string]::IsNullOrWhiteSpace($line)) { continue }
            $columns = $line -split "`t"
            if ($columns.Count -ge 3) {
                $tags += $columns[2].Trim()
            }
        }
    }
    return @($tags | Where-Object { $_ } | Select-Object -Unique)
}

function ConvertTo-VersionObject {
    param([string] $VersionText)

    try {
        return [version]$VersionText
    }
    catch {
        return $null
    }
}

function Get-MaxLocalVersionText {
    param([string] $Root)

    $found = @()

    $localRoot = Join-Path $Root 'local'
    if (Test-Path -LiteralPath $localRoot) {
        Get-ChildItem -LiteralPath $localRoot -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^release-v(\d+\.\d+(?:\.\d+)?)$' } |
            ForEach-Object {
                $null = $_.Name -match '^release-v(\d+\.\d+(?:\.\d+)?)$'
                $found += $Matches[1]
            }
    }

    $notesRoot = Join-Path $Root 'release'
    if (Test-Path -LiteralPath $notesRoot) {
        Get-ChildItem -LiteralPath $notesRoot -Filter 'notes-v*.md' -File -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -match '^notes-v(\d+\.\d+(?:\.\d+)?)\.md$' } |
            ForEach-Object {
                $null = $_.Name -match '^notes-v(\d+\.\d+(?:\.\d+)?)\.md$'
                $found += $Matches[1]
            }
    }

    if (-not $found) { return $null }

    return (
        $found |
            ForEach-Object { [pscustomobject]@{ Text = $_; SortKey = ConvertTo-VersionObject $_ } } |
            Where-Object { $null -ne $_.SortKey } |
            Sort-Object SortKey -Descending |
            Select-Object -First 1 -ExpandProperty Text
    )
}

function Get-NextVersionText {
    param(
        [string[]] $ExistingTags,
        [string] $Root
    )

    $versionTexts = @()
    foreach ($tagName in $ExistingTags) {
        if ($tagName -match '^v(\d+\.\d+(?:\.\d+)?)$') {
            $versionTexts += $Matches[1]
        }
    }

    $baseText = $null
    if ($versionTexts.Count -gt 0) {
        $baseText = (
            $versionTexts |
                ForEach-Object { [pscustomobject]@{ Text = $_; SortKey = ConvertTo-VersionObject $_ } } |
                Where-Object { $null -ne $_.SortKey } |
                Sort-Object SortKey -Descending |
                Select-Object -First 1 -ExpandProperty Text
        )
    }
    else {
        $baseText = Get-MaxLocalVersionText -Root $Root
    }

    if (-not $baseText) {
        return '1.0'
    }

    $parts = $baseText.Split('.')
    $parts[$parts.Length - 1] = [string](([int]$parts[$parts.Length - 1]) + 1)
    return ($parts -join '.')
}

function Get-LastCommitSubject {
    $subject = git log -1 --pretty=%s
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($subject)) {
        throw 'Não foi possível ler a mensagem do último commit (git log -1 --pretty=%s).'
    }
    return $subject.Trim()
}

if (-not $RepoRoot) {
    # scripts -> publish-release -> skills -> .cursor -> repo root
    $RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..\..\..\..')).Path
}

Set-Location -LiteralPath $RepoRoot

$gh = Resolve-GhExe -ExplicitPath $GhPath
Write-Host "Usando gh: $gh"
& $gh auth status
if ($LASTEXITCODE -ne 0) {
    throw 'gh não autenticado. Rode: gh auth login'
}

$existingTags = Get-ExistingReleaseTags -GhExe $gh

if (-not $Version) {
    $Version = Get-NextVersionText -ExistingTags $existingTags -Root $RepoRoot
}

if (-not $Title) {
    $Title = Get-LastCommitSubject
}

$tag = "v$Version"
$releaseDir = Join-Path $RepoRoot "local\release-$tag"
$notesFile = Join-Path $RepoRoot "release\notes-$tag.md"

Write-Host "Versão: $tag"
Write-Host "Título: $Title"

if (-not (Test-ReleasePackageComplete -ReleaseDir $releaseDir -NotesFile $notesFile)) {
    throw @"
Pacote incompleto para $tag.
Esperado:
  $releaseDir\ (6 artefatos)
  $notesFile
"@
}

$assetPaths = foreach ($assetName in $script:RequiredAssets) {
    Join-Path $releaseDir $assetName
}

if ($Push -and -not $SkipPush) {
    Write-Host 'Push da branch atual...'
    git push -u origin HEAD
    if ($LASTEXITCODE -ne 0) {
        throw 'git push falhou; release não criada.'
    }
}

if ($existingTags -contains $tag) {
    throw "Release/tag $tag já existe. Algo está inconsistente com o cálculo da próxima versão."
}

Write-Host "Criando release $tag ..."
& $gh release create $tag @assetPaths `
    --title $Title `
    --notes-file $notesFile `
    --latest
if ($LASTEXITCODE -ne 0) {
    throw "Falha ao criar release $tag"
}

$tagsToDelete = @($existingTags | Where-Object { $_ -and $_ -ne $tag } | Select-Object -Unique)
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
