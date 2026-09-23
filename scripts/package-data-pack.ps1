param(
  [string]$SourceRoot = '',
  [string]$OutputRoot = ''
)

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'release-paths.ps1')
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'stop-packaging-processes.ps1') -WorkspaceRoot $projectRoot
if ($LASTEXITCODE -ne 0) { throw 'Failed to stop packaging-conflicting project processes.' }
if (-not $SourceRoot) { $SourceRoot = Join-Path $projectRoot 'app-data' }
if (-not $OutputRoot) { $OutputRoot = Join-Path $releaseRoot "data-pack-$releaseVersion" }
Assert-NewArtifact $OutputRoot

$source = (Resolve-Path -LiteralPath $SourceRoot).Path
$output = [System.IO.Path]::GetFullPath($OutputRoot).TrimEnd('\')
$projectFull = [System.IO.Path]::GetFullPath($projectRoot).TrimEnd('\')
if ($output -notlike "$projectFull\dist-installer\*") {
  throw "Refusing to write data pack outside dist-installer: $output"
}
if ($output -eq [System.IO.Path]::GetFullPath($source).TrimEnd('\')) {
  throw 'Source and data-pack output are identical.'
}

$statusFile = Join-Path $source 'status\tdx-daily-history.json'
if (-not (Test-Path -LiteralPath $statusFile)) { throw "Missing daily status: $statusFile" }
$statusJson = [System.IO.File]::ReadAllText($statusFile, [System.Text.Encoding]::UTF8)
$status = $statusJson | ConvertFrom-Json
$tradeDate = [string]$status.trade_date
if ($tradeDate -notmatch '^\d{8}$') { throw "Invalid latest trade date in status: $tradeDate" }
$resourceLibraryTarget = 'selected-client-directory\data\resource-library'

$canonicalRelative = 'market\daily\aggregate\tdx-bars.jsonl'
$latestDaySource = Join-Path $source "market\daily\$tradeDate"
$latestManifestSource = Join-Path $latestDaySource 'manifest.json'
$latestIndexSource = Join-Path $latestDaySource 'daily-data-index.json'
$latestArchiveSource = Join-Path $latestDaySource 'tdx-bars.jsonl'
if (-not (Test-Path -LiteralPath $latestManifestSource)) { throw "Missing latest daily manifest: $latestManifestSource" }
if (-not (Test-Path -LiteralPath $latestIndexSource)) { throw "Missing latest daily index: $latestIndexSource" }
if (-not (Test-Path -LiteralPath $latestArchiveSource)) { throw "Missing latest daily archive: $latestArchiveSource" }

# Build the byte-range index from the full-history source before copying the
# data pack.  The data installer then ships the index together with the
# canonical JSONL, so first launch does not need to scan several GB merely to
# locate one stock.  The desktop button can still force a rebuild later.
$canonicalIndexSource = Join-Path $source 'market\daily\index\canonical-symbol-index.json'
$indexScript = Join-Path $projectRoot 'scripts\build-canonical-daily-index.mjs'
& node $indexScript $latestArchiveSource $canonicalIndexSource
if ($LASTEXITCODE -ne 0) { throw "Canonical daily index build failed with exit code $LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $canonicalIndexSource -PathType Leaf)) { throw "Canonical daily index was not generated: $canonicalIndexSource" }

New-Item -ItemType Directory -Path $output -Force | Out-Null

function Copy-DataFile([string]$relativePath, [string]$targetRelativePath = $relativePath) {
  $sourcePath = Join-Path $source $relativePath
  if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) { throw "Missing required data file: $sourcePath" }
  $targetPath = Join-Path $output $targetRelativePath
  $targetDirectory = Split-Path -Parent $targetPath
  New-Item -ItemType Directory -Path $targetDirectory -Force | Out-Null
  Copy-Item -LiteralPath $sourcePath -Destination $targetPath -Force
}

function Copy-DataDirectory([string]$relativePath) {
  $sourcePath = Join-Path $source $relativePath
  if (-not (Test-Path -LiteralPath $sourcePath -PathType Container)) { throw "Missing required data directory: $sourcePath" }
  $targetPath = Join-Path $output $relativePath
  New-Item -ItemType Directory -Path $targetPath -Force | Out-Null
  & robocopy.exe $sourcePath $targetPath /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /XF '*.lc5' '*.LC5' /NFL /NDL /NP
  $robocopyCode = $LASTEXITCODE
  if ($robocopyCode -gt 7) { throw "robocopy failed for $relativePath with exit code $robocopyCode" }
}

function Get-Sha256([string]$filePath) {
  $algorithm = [System.Security.Cryptography.SHA256]::Create()
  $stream = [System.IO.File]::OpenRead($filePath)
  try {
    return ([System.BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '')).ToLowerInvariant()
  } finally {
    $stream.Dispose()
    $algorithm.Dispose()
  }
}

# The latest verified trade-date archive is the only full-history copy. Older
# trade-date folders and the stale aggregate are intentionally not copied.
Copy-DataFile "market\daily\$tradeDate\tdx-bars.jsonl" $canonicalRelative
Copy-DataFile 'market\daily\index\tdx-symbol-index.json'
Copy-DataFile 'market\daily\index\canonical-symbol-index.json'
Copy-DataFile 'market\daily\index\daily-data-index.json'
Copy-DataFile "market\daily\$tradeDate\manifest.json"
Copy-DataFile "market\daily\$tradeDate\daily-data-index.json"
Copy-DataFile 'status\tdx-daily-history.json'

if (Test-Path -LiteralPath (Join-Path $source 'market\daily\fallback') -PathType Container) {
  Copy-DataDirectory 'market\daily\fallback'
}
Copy-DataFile "market\security-master\$tradeDate.jsonl"

$formulaPackage = Join-Path $source 'evidence\formulas\package'
if (Test-Path -LiteralPath $formulaPackage -PathType Container) {
  Copy-DataDirectory 'evidence\formulas\package'
}

# Formula source files are portable inputs, but the per-stock TQ receipts are
# also needed on a clean client: without them a whiteboard TDX installation
# has no local evidence that the five required formulas were executed before
# the data pack was created. Keep the receipts in the writable data library;
# never write them back into the TDX source directory.
$formulaEvidence = Join-Path $source 'evidence\formulas'
if (Test-Path -LiteralPath $formulaEvidence -PathType Container) {
  Get-ChildItem -LiteralPath $formulaEvidence -Recurse -File -Force |
    Where-Object { $_.FullName -notlike "$formulaPackage\*" -and $_.Extension -ieq '.json' } |
    ForEach-Object {
      $relative = $_.FullName.Substring($source.Length + 1)
      Copy-DataFile $relative
    }
}

# These are small, date-addressable public fallback layers required by the
# catalog skills. Omitting them makes a data installer look successful while
# every chat preflight on a clean machine reports the assets as missing.
foreach ($relativeDirectory in @('evidence\public', 'public\limit-up', 'public\lhb')) {
  if (Test-Path -LiteralPath (Join-Path $source $relativeDirectory) -PathType Container) {
    Copy-DataDirectory $relativeDirectory
  }
}

# Stable entry points are used by home/chat preflight, not only dated files.
foreach ($relativeFile in @('public\latest.json', 'news\latest.json', 'evidence\public\latest.json')) {
  if (Test-Path -LiteralPath (Join-Path $source $relativeFile) -PathType Leaf) { Copy-DataFile $relativeFile }
}

$integrityFiles = @(Get-ChildItem -LiteralPath (Join-Path $source 'runtime') -Filter 'daily-jsonl-integrity-*.json' -File -ErrorAction SilentlyContinue)
foreach ($file in $integrityFiles) {
  Copy-DataFile (Join-Path 'runtime' $file.Name)
}

$iconSource = Join-Path $projectRoot 'packaging\data-pack-icon.png'
if (-not (Test-Path -LiteralPath $iconSource -PathType Leaf)) { throw "Missing data-pack icon: $iconSource" }
Copy-Item -LiteralPath $iconSource -Destination (Join-Path $output 'icon.png') -Force
$readmeSource = Join-Path $projectRoot 'packaging\data-pack-README.md'
if (-not (Test-Path -LiteralPath $readmeSource -PathType Leaf)) { throw "Missing data-pack README: $readmeSource" }
Copy-Item -LiteralPath $readmeSource -Destination (Join-Path $output 'README.md') -Force

$allFiles = @(Get-ChildItem -LiteralPath $output -Recurse -File -Force)
$minuteFiles = @($allFiles | Where-Object { $_.Extension -ieq '.lc5' })
if ($minuteFiles.Count -gt 0) { throw "Data pack contains forbidden raw minute files: $($minuteFiles.FullName -join ', ')" }
$bytes = [int64](($allFiles | Measure-Object -Property Length -Sum).Sum)
$canonicalTarget = Join-Path $output $canonicalRelative
$canonicalSourceHash = [string]$status.sha256
$canonicalTargetHash = Get-Sha256 $canonicalTarget
if ($canonicalSourceHash -and $canonicalSourceHash.ToLowerInvariant() -ne $canonicalTargetHash) {
  throw "Canonical archive hash mismatch after copy: expected $canonicalSourceHash, got $canonicalTargetHash"
}

$manifest = [ordered]@{
  schema = 'ZHANGCAI_DESKTOP_DATA_PACK_V1'
  product = 'Zhangcai Desktop'
  packageVersion = $releaseVersion
  icon = 'icon.png'
  generatedAt = (Get-Date).ToUniversalTime().ToString('o')
  sourceRoot = $source
  latestTradeDate = $tradeDate
  dataPolicy = 'canonical-daily-only; no-duplicate-full-snapshots; minute-data-on-demand-external'
  canonicalDaily = [ordered]@{
    path = 'market/daily/aggregate/tdx-bars.jsonl'
  sourceSha256 = $canonicalTargetHash
  sourceManifestSha256 = $canonicalSourceHash
    sourceArchive = "market/daily/$tradeDate/tdx-bars.jsonl"
    length = (Get-Item -LiteralPath $canonicalTarget).Length
  }
  included = @(
    'market/daily/aggregate/tdx-bars.jsonl',
    'market/daily/index/tdx-symbol-index.json',
    'market/daily/index/canonical-symbol-index.json',
    'market/daily/index/daily-data-index.json',
    "market/daily/$tradeDate/manifest.json",
    "market/daily/$tradeDate/daily-data-index.json",
     'market/daily/fallback/<trade-date>/*.jsonl',
     "market/security-master/$tradeDate.jsonl",
     'evidence/formulas/package/*',
     'evidence/formulas/<trade-date>/*.json',
     'evidence/public/*.json',
     'public/limit-up/*.json',
     'public/lhb/*.json',
     'runtime/daily-jsonl-integrity-*.json',
    'icon.png',
    'README.md'
  )
  excluded = @('older duplicate full-history trade-date archives', '*.lc5', '*.LC5', 'DeepSeek credentials', 'program code and runtimes')
  payloadFileCount = $allFiles.Count
  payloadBytes = $bytes
  installTarget = $resourceLibraryTarget
   importRule = 'merge market/status/evidence/public/evidence/formulas/public/runtime into the resource-library root; keep this data-pack manifest, icon and README beside the installer; never overwrite resource-library/manifest.json or embedded code/runtimes; never modify the selected TDX source directory'
}
$manifest | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $output 'manifest.json') -Encoding UTF8

[pscustomobject]@{
  status = 'PASS'
  output = $output
  latestTradeDate = $tradeDate
  payloadFiles = $allFiles.Count
  payloadBytes = $bytes
  gigabytes = [math]::Round($bytes / 1GB, 3)
  canonicalSha256 = $canonicalTargetHash
  rawMinuteFiles = $minuteFiles.Count
  duplicateFullHistoryFoldersExcluded = $true
} | ConvertTo-Json -Depth 6
