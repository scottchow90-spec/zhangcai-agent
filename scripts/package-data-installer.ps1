param(
  [string]$SourceRoot = '',
  [string]$OutputFile = ''
)

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'release-paths.ps1')
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'stop-packaging-processes.ps1') -WorkspaceRoot $projectRoot
if ($LASTEXITCODE -ne 0) { throw 'Failed to stop packaging-conflicting project processes.' }
if (-not $SourceRoot) { $SourceRoot = Join-Path $releaseRoot "data-pack-$releaseVersion" }

$source = (Resolve-Path -LiteralPath $SourceRoot).Path.TrimEnd('\')
$distRoot = [System.IO.Path]::GetFullPath($releaseRoot).TrimEnd('\')
$output = if ($OutputFile) {
  if ([System.IO.Path]::IsPathRooted($OutputFile)) { [System.IO.Path]::GetFullPath($OutputFile) } else { [System.IO.Path]::GetFullPath((Join-Path $projectRoot $OutputFile)) }
} else {
  Join-Path $distRoot "掌财桌面端-日线数据包-$releaseVersion-x64.exe"
}
Assert-NewArtifact $output
if ($source -notlike "$distRoot\data-pack-*") {
  throw "Refusing to embed a data pack outside dist-installer: $source"
}
if ($output -notlike "$distRoot\*") {
  throw "Refusing to write data installer outside dist-installer: $output"
}

$requiredDirectories = @('market', 'status', 'evidence', 'public', 'runtime')
foreach ($directory in $requiredDirectories) {
  $path = Join-Path $source $directory
  if (-not (Test-Path -LiteralPath $path -PathType Container)) {
    throw "Data pack is missing required directory: $path"
  }
}
$forbiddenMinuteFiles = @(Get-ChildItem -LiteralPath $source -Recurse -File -Force | Where-Object { $_.Extension -ieq '.lc5' })
if ($forbiddenMinuteFiles.Count -gt 0) {
  throw "Refusing to package raw minute data: $($forbiddenMinuteFiles.FullName -join ', ')"
}

$iconScript = Join-Path $projectRoot 'scripts\convert-data-pack-icon.mjs'
& node $iconScript
if ($LASTEXITCODE -ne 0) { throw "Data pack icon generation failed with exit code $LASTEXITCODE" }

$icon = (Resolve-Path -LiteralPath (Join-Path $projectRoot 'packaging\data-pack-icon.ico')).Path
$nsi = (Resolve-Path -LiteralPath (Join-Path $projectRoot 'electron-app\nsis\data-pack-installer.nsi')).Path
$payloadName = "zhangcai-daily-data-$releaseVersion.7z"
$payload = Join-Path $distRoot $payloadName
$payloadTemp = Join-Path $distRoot "zhangcai-daily-data-$releaseVersion.tmp.7z"
$compileOutput = Join-Path $distRoot "data-pack-installer-$releaseVersion-x64.exe"

function Get-ShortPath([string]$path) {
  $fso = New-Object -ComObject Scripting.FileSystemObject
  if (Test-Path -LiteralPath $path -PathType Container) {
    return $fso.GetFolder($path).ShortPath
  }
  if (Test-Path -LiteralPath $path -PathType Leaf) {
    return $fso.GetFile($path).ShortPath
  }
  $parent = Split-Path -Parent $path
  if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
    throw "Cannot resolve short path because parent directory is missing: $parent"
  }
  return (Join-Path $fso.GetFolder($parent).ShortPath (Split-Path -Leaf $path))
}

$sevenZipCandidates = @(Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'electron-builder\Cache') -Recurse -Filter '7za.exe' -File -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)
$sevenZip = $sevenZipCandidates | Select-Object -First 1
if (-not $sevenZip) { throw '7za.exe was not found in the electron-builder cache.' }
$makensisCandidates = @(Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'electron-builder\Cache\nsis') -Recurse -Filter 'makensis.exe' -File -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)
$makensis = $makensisCandidates | Select-Object -First 1
if (-not $makensis) { throw 'makensis.exe was not found in the electron-builder NSIS cache.' }

Assert-NewArtifact $output
if (Test-Path -LiteralPath $compileOutput -PathType Leaf) {
  Remove-Item -LiteralPath $compileOutput -Force
}
if (Test-Path -LiteralPath $payload -PathType Leaf) {
  Remove-Item -LiteralPath $payload -Force
}
if (Test-Path -LiteralPath $payloadTemp -PathType Leaf) {
  Remove-Item -LiteralPath $payloadTemp -Force
}

$outputForNsis = Get-ShortPath $compileOutput
$iconForNsis = Get-ShortPath $icon
$nsiForNsis = Get-ShortPath $nsi
$payloadTempForSevenZip = Get-ShortPath $payloadTemp
$sourceForSevenZip = Get-ShortPath $source

Write-Output "Creating external 7z payload: $payload"
Write-Output "7-Zip compressor: $($sevenZip.FullName)"
Push-Location $sourceForSevenZip
try {
  $payloadRoots = @($requiredDirectories)
  if (Test-Path -LiteralPath (Join-Path $source 'news')) { $payloadRoots += 'news' }
  & $sevenZip.FullName 'a' $payloadTempForSevenZip @payloadRoots '-mx=1' '-mmt=on' '-m0=lzma2' '-md=8m' '-ms=on' '-y'
  if ($LASTEXITCODE -ne 0) { throw "7-Zip data payload build failed with exit code $LASTEXITCODE" }
} finally {
  Pop-Location
}
if (-not (Test-Path -LiteralPath $payloadTemp -PathType Leaf)) { throw "7-Zip completed without creating: $payloadTemp" }
Move-Item -LiteralPath $payloadTemp -Destination $payload -Force
& $sevenZip.FullName 't' (Get-ShortPath $payload) '-y'
if ($LASTEXITCODE -ne 0) { throw "7-Zip payload integrity test failed with exit code $LASTEXITCODE" }

$payloadFileBytes = (Get-Item -LiteralPath $payload).Length
$payloadPartSize = [int64][math]::Ceiling($payloadFileBytes / 4)
$payloadParts = @()
$inputStream = [System.IO.File]::OpenRead($payload)
try {
  $buffer = New-Object byte[] (4MB)
  for ($partIndex = 1; $partIndex -le 4; $partIndex++) {
    $partPath = Join-Path $distRoot ("data-pack-installer-payload.part{0}" -f $partIndex)
    if (Test-Path -LiteralPath $partPath -PathType Leaf) { Remove-Item -LiteralPath $partPath -Force }
    $outputStream = [System.IO.File]::Open($partPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
    try {
      $remaining = [int64][math]::Min($payloadPartSize, $payloadFileBytes - $inputStream.Position)
      while ($remaining -gt 0) {
        $requested = [int][math]::Min($buffer.Length, $remaining)
        $read = $inputStream.Read($buffer, 0, $requested)
        if ($read -le 0) { throw "Unexpected end of data while splitting payload at part $partIndex." }
        $outputStream.Write($buffer, 0, $read)
        $remaining -= $read
      }
    } finally {
      $outputStream.Dispose()
    }
    $payloadParts += $partPath
  }
} finally {
  $inputStream.Dispose()
}
Write-Output "NSIS compiler: $($makensis.FullName)"
Write-Output "Output: $output"
Write-Output "NSIS source paths use 8.3 aliases to support the Chinese workspace path."
& $makensis.FullName '/V2' "/DZHANGCAI_OUTPUT=$outputForNsis" "/DZHANGCAI_DATA_PACK_ICO=$iconForNsis" "/DZHANGCAI_7ZA=$(Get-ShortPath $sevenZip.FullName)" "/DZHANGCAI_DATA_PAYLOAD_PART1=$($payloadParts[0])" "/DZHANGCAI_DATA_PAYLOAD_PART2=$($payloadParts[1])" "/DZHANGCAI_DATA_PAYLOAD_PART3=$($payloadParts[2])" "/DZHANGCAI_DATA_PAYLOAD_PART4=$($payloadParts[3])" $nsiForNsis
if ($LASTEXITCODE -ne 0) { throw "NSIS data installer build failed with exit code $LASTEXITCODE" }
if (-not (Test-Path -LiteralPath $compileOutput -PathType Leaf)) { throw "NSIS completed without creating: $compileOutput" }
Assert-NewArtifact $output
[System.IO.File]::Move($compileOutput, $output)
if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw "Failed to finalize data installer: $output" }

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

$file = Get-Item -LiteralPath $output
$payloadFile = Get-Item -LiteralPath $payload
$payloadBytes = $payloadFile.Length
$payloadSha256 = Get-Sha256 $payload
Remove-Item -LiteralPath $payload -Force
foreach ($partPath in $payloadParts) {
  if (Test-Path -LiteralPath $partPath -PathType Leaf) { Remove-Item -LiteralPath $partPath -Force }
}
[pscustomobject]@{
  status = 'PASS'
  artifact = $output
  bytes = $file.Length
  gigabytes = [math]::Round($file.Length / 1GB, 3)
  sha256 = Get-Sha256 $output
  embeddedPayloadBytes = $payloadBytes
  embeddedPayloadGigabytes = [math]::Round($payloadBytes / 1GB, 3)
  embeddedPayloadSha256 = $payloadSha256
  payloadExternalArtifact = $false
  source = $source
  targetAtInstall = 'selected-client-directory\data\resource-library (the selected client directory is validated and recorded)'
  includedRoots = $requiredDirectories
  rawMinuteFiles = 0
} | ConvertTo-Json -Depth 6
