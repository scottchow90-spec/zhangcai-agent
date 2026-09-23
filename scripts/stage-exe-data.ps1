param(
  [string]$SourceRoot = '',
  [string]$UnpackedRoot = ''
)

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (-not $SourceRoot) { $SourceRoot = Join-Path $projectRoot 'app-data' }
if (-not $UnpackedRoot) { $UnpackedRoot = Join-Path $projectRoot 'dist-installer\win-unpacked' }

$source = (Resolve-Path -LiteralPath $SourceRoot).Path
$unpacked = (Resolve-Path -LiteralPath $UnpackedRoot).Path
$target = Join-Path $unpacked 'resources\resource-library'
$sourceFull = [System.IO.Path]::GetFullPath($source).TrimEnd('\')
$targetFull = [System.IO.Path]::GetFullPath($target).TrimEnd('\')
if ($sourceFull -eq $targetFull) { throw 'Refusing to stage EXE data because source and target are identical.' }
if (-not (Test-Path -LiteralPath $target)) { New-Item -ItemType Directory -Path $target -Force | Out-Null }

$sourceBytes = [int64]((Get-ChildItem -LiteralPath $source -Recurse -File -Force | Measure-Object -Property Length -Sum).Sum)
$sourceFiles = (Get-ChildItem -LiteralPath $source -Recurse -File -Force | Measure-Object).Count
Write-Output ("Staging {0} files ({1} GB) into {2}" -f $sourceFiles, [math]::Round($sourceBytes / 1GB, 3), $target)

$excludedPatterns = @('*.lc5', '*.LC5')
& robocopy.exe $source $target /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /XF $excludedPatterns /NFL /NDL /NP
$robocopyCode = $LASTEXITCODE
if ($robocopyCode -gt 7) { throw "robocopy failed with exit code $robocopyCode" }

$staged = @(Get-ChildItem -LiteralPath $target -Recurse -File -Force)
$stagedBytes = [int64](($staged | Measure-Object -Property Length -Sum).Sum)
$stagedMinuteFiles = @($staged | Where-Object { $_.Extension -ieq '.lc5' })
if ($stagedMinuteFiles.Count -gt 0) {
  throw ("EXE resource staging must not include raw 5-minute files: " + ($stagedMinuteFiles.FullName -join ', '))
}
$required = @(
  'status\tdx-daily-history.json',
  'market\daily\index\tdx-symbol-index.json',
  'evidence\formulas\package\manifest.json'
)
$missing = @($required | Where-Object { -not (Test-Path -LiteralPath (Join-Path $target $_)) })
if ($missing.Count -gt 0) { throw ('Staged data is missing required files: ' + ($missing -join ', ')) }

[pscustomobject]@{
  status = 'PASS'
  source = $source
  target = $target
  sourceFiles = $sourceFiles
  sourceBytes = $sourceBytes
  stagedFiles = $staged.Count
  stagedBytes = $stagedBytes
  rawMinuteFilesExcluded = $true
  excludedPatterns = $excludedPatterns
  robocopyExitCode = $robocopyCode
  requiredFiles = $required
} | ConvertTo-Json -Depth 6
