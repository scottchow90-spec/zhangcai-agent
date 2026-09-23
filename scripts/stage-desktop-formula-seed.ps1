param(
  [string]$SourceRoot = '',
  [string]$TargetRoot = ''
)

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (-not $SourceRoot) { $SourceRoot = Join-Path $projectRoot 'app-data\evidence\formulas\package' }
if (-not $TargetRoot) { $TargetRoot = Join-Path $projectRoot 'electron-app\resource-library\evidence\formulas\package' }
$source = (Resolve-Path -LiteralPath $SourceRoot).Path
$target = [System.IO.Path]::GetFullPath($TargetRoot).TrimEnd('\')

$manifestSource = Join-Path $source 'manifest.json'
if (-not (Test-Path -LiteralPath $manifestSource -PathType Leaf)) {
  throw "Portable formula seed manifest is missing: $manifestSource"
}
$manifest = Get-Content -LiteralPath $manifestSource -Raw -Encoding UTF8 | ConvertFrom-Json
$required = @($manifest.required_files | ForEach-Object { ([string]$_).Replace('/', '\') })
if ($required.Count -eq 0) { throw "Portable formula seed has no required_files: $manifestSource" }

New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item -LiteralPath $manifestSource -Destination (Join-Path $target 'manifest.json') -Force
foreach ($relative in $required) {
  $sourceFile = Join-Path $source $relative
  if (-not (Test-Path -LiteralPath $sourceFile -PathType Leaf)) {
    throw "Portable formula seed is incomplete; missing: $sourceFile"
  }
  $targetFile = Join-Path $target $relative
  New-Item -ItemType Directory -Path (Split-Path -Parent $targetFile) -Force | Out-Null
  Copy-Item -LiteralPath $sourceFile -Destination $targetFile -Force
}

$unexpectedMinuteFiles = @(Get-ChildItem -LiteralPath $target -Recurse -File -Force | Where-Object { $_.Extension -ieq '.lc5' })
if ($unexpectedMinuteFiles.Count -gt 0) {
  throw "Formula seed must not contain raw minute files: $($unexpectedMinuteFiles.FullName -join ', ')"
}

$files = @(Get-ChildItem -LiteralPath $target -Recurse -File -Force)
$bytes = [int64](($files | Measure-Object -Property Length -Sum).Sum)
[pscustomobject]@{
  status = 'PASS'
  source = $source
  target = $target
  manifest = (Join-Path $target 'manifest.json')
  requiredFiles = $required.Count
  stagedFiles = $files.Count
  bytes = $bytes
  rawMinuteFiles = 0
} | ConvertTo-Json -Depth 6
