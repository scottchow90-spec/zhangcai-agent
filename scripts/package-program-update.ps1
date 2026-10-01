param(
  [string]$ProgramSourceRoot = '',
  [string]$EnvironmentClientRoot = '',
  [string]$OutputFile = ''
)

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'release-paths.ps1')

$unpackedRoot = if ($ProgramSourceRoot) { $ProgramSourceRoot } else { Join-Path $releaseRoot 'win-unpacked' }
if (-not (Test-Path -LiteralPath $unpackedRoot -PathType Container)) {
  throw "Missing program payload source: $unpackedRoot. Supply -ProgramSourceRoot or build the current version first."
}
$unpackedRoot = (Resolve-Path -LiteralPath $unpackedRoot).Path.TrimEnd('\')
$resourcesRoot = Join-Path $unpackedRoot 'resources'
$appSource = Join-Path $resourcesRoot 'app'
$programAsar = Join-Path $resourcesRoot 'app.asar'
$embeddedResourceLibrary = Join-Path $resourcesRoot 'resource-library'
foreach ($required in @($programAsar, $appSource, $embeddedResourceLibrary)) {
  if (-not (Test-Path -LiteralPath $required)) { throw "Current program build is incomplete: $required" }
}

function Assert-EnvironmentRoot([string]$clientRoot) {
  if (-not $clientRoot) { return }
  $resolved = (Resolve-Path -LiteralPath $clientRoot).Path.TrimEnd('\')
  $clientExe = @(Get-ChildItem -LiteralPath $resolved -Filter '*.exe' -File -ErrorAction SilentlyContinue | Select-Object -First 1)
  $required = @(
    (Join-Path $resolved 'resources\runtime\node\node.exe'),
    (Join-Path $resolved 'resources\runtime\python\python.exe'),
    (Join-Path $resolved 'resources\deepseek-harness\lib\bin.js'),
    (Join-Path $resolved 'resources\app\node_modules\vinext\dist\cli.js')
  )
  $missing = @($required | Where-Object { -not (Test-Path -LiteralPath $_) })
  if ($clientExe.Count -eq 0) { $missing += (Join-Path $resolved '*.exe') }
  if ($missing.Count -gt 0) {
    throw "Environment layer is incomplete; program update is refused. Missing: $($missing -join ', ')"
  }
  Write-Output "Environment reuse check: PASS ($resolved)"
}

Assert-EnvironmentRoot $EnvironmentClientRoot

$output = if ($OutputFile) {
  if ([System.IO.Path]::IsPathRooted($OutputFile)) { [System.IO.Path]::GetFullPath($OutputFile) } else { [System.IO.Path]::GetFullPath((Join-Path $projectRoot $OutputFile)) }
} else {
  $productName = -join @([char]0x638C, [char]0x8D22, [char]0x684C, [char]0x9762, [char]0x7AEF)
  $updateLabel = -join @([char]0x7A0B, [char]0x5E8F, [char]0x66F4, [char]0x65B0)
  Join-Path $releaseRoot ($productName + '-' + $updateLabel + '-' + $releaseVersion + '-x64.exe')
}
Assert-NewArtifact $output
if ($output -notlike (([System.IO.Path]::GetFullPath($releaseRoot)).TrimEnd('\') + '\*')) {
  throw "Refusing to write program update outside the current release directory: $output"
}

function Get-ShortPath([string]$path) {
  $fso = New-Object -ComObject Scripting.FileSystemObject
  if (Test-Path -LiteralPath $path -PathType Container) { return $fso.GetFolder($path).ShortPath }
  if (Test-Path -LiteralPath $path -PathType Leaf) { return $fso.GetFile($path).ShortPath }
  $parent = Split-Path -Parent $path
  if (-not (Test-Path -LiteralPath $parent -PathType Container)) { throw "Missing path for 8.3 conversion: $path" }
  return (Join-Path $fso.GetFolder($parent).ShortPath (Split-Path -Leaf $path))
}

function Invoke-Robocopy([string]$source, [string]$destination, [string[]]$excludeDirectories = @()) {
  New-Item -ItemType Directory -Path $destination -Force | Out-Null
  $arguments = @($source, $destination, '/E', '/COPY:DAT', '/DCOPY:DAT', '/R:1', '/W:1', '/XJ', '/NFL', '/NDL', '/NJH', '/NJS', '/NP')
  if ($excludeDirectories.Count -gt 0) { $arguments += @('/XD') + $excludeDirectories }
  & robocopy.exe @arguments | Out-Null
  if ($LASTEXITCODE -gt 7) { throw "Robocopy failed ($LASTEXITCODE): $source -> $destination" }
}

function Get-Sha256([string]$filePath) {
  $algorithm = [System.Security.Cryptography.SHA256]::Create()
  $stream = [System.IO.File]::OpenRead($filePath)
  try { return ([System.BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '')).ToLowerInvariant() }
  finally { $stream.Dispose(); $algorithm.Dispose() }
}

$sevenZip = @(Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'electron-builder\Cache') -Recurse -Filter '7za.exe' -File -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1)
if (-not $sevenZip) { throw '7za.exe was not found in the electron-builder cache.' }
$makensis = @(Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'electron-builder\Cache\nsis') -Recurse -Filter 'makensis.exe' -File -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1)
if (-not $makensis) { throw 'makensis.exe was not found in the electron-builder NSIS cache.' }
$icon = (Resolve-Path -LiteralPath (Join-Path $projectRoot 'electron-app\resources\installer-icon.ico')).Path
$nsi = (Resolve-Path -LiteralPath (Join-Path $projectRoot 'electron-app\nsis\program-update-installer.nsi')).Path

$staging = Join-Path $releaseRoot ('.program-update-staging-' + [guid]::NewGuid().ToString('N'))
$payload = Join-Path $releaseRoot "zhangcai-program-$releaseVersion.7z"
$payloadTemp = Join-Path $releaseRoot "zhangcai-program-$releaseVersion.tmp.7z"
$compileOutput = Join-Path $releaseRoot "program-update-installer-$releaseVersion-x64.exe"
$payloadParts = @()
Assert-NewArtifact $payload
Assert-NewArtifact $payloadTemp
Assert-NewArtifact $compileOutput
for ($index = 1; $index -le 4; $index++) {
  Assert-NewArtifact (Join-Path $releaseRoot ("pupd{0}.bin" -f $index))
}

try {
  New-Item -ItemType Directory -Path (Join-Path $staging 'resources') -Force | Out-Null
  Copy-Item -LiteralPath $programAsar -Destination (Join-Path $staging 'resources\app.asar') -Force
  Invoke-Robocopy $appSource (Join-Path $staging 'resources\app') @((Join-Path $appSource 'node_modules'))
  Invoke-Robocopy $embeddedResourceLibrary (Join-Path $staging 'resources\resource-library')

  $stagingShort = Get-ShortPath $staging
  $payloadTempShort = Get-ShortPath $payloadTemp
  Write-Output "Creating program-only payload: $payloadTemp"
  Push-Location $stagingShort
  try {
    & $sevenZip[0].FullName 'a' $payloadTempShort 'resources' '-mx=1' '-mmt=on' '-m0=lzma2' '-md=8m' '-ms=on' '-y'
    if ($LASTEXITCODE -ne 0) { throw "Program payload build failed with exit code $LASTEXITCODE" }
  } finally { Pop-Location }
  Move-Item -LiteralPath $payloadTemp -Destination $payload -Force
  & $sevenZip[0].FullName 't' (Get-ShortPath $payload) '-y'
  if ($LASTEXITCODE -ne 0) { throw "Program payload integrity test failed with exit code $LASTEXITCODE" }

  $payloadBytes = (Get-Item -LiteralPath $payload).Length
  $partSize = [int64][math]::Ceiling($payloadBytes / 4)
  $input = [System.IO.File]::OpenRead($payload)
  try {
    $buffer = New-Object byte[] (4MB)
    for ($index = 1; $index -le 4; $index++) {
      $partPath = Join-Path $releaseRoot ("pupd{0}.bin" -f $index)
      $outputStream = [System.IO.File]::Open($partPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
      try {
        $remaining = [int64][math]::Min($partSize, $payloadBytes - $input.Position)
        while ($remaining -gt 0) {
          $requested = [int][math]::Min($buffer.Length, $remaining)
          $read = $input.Read($buffer, 0, $requested)
          if ($read -le 0) { throw "Unexpected end of program payload at part $index." }
          $outputStream.Write($buffer, 0, $read)
          $remaining -= $read
        }
      } finally { $outputStream.Dispose() }
      $payloadParts += $partPath
    }
  } finally { $input.Dispose() }

  $outputShort = Get-ShortPath $compileOutput
  $iconShort = Get-ShortPath $icon
  $nsiShort = Get-ShortPath $nsi
  $sevenZipShort = Get-ShortPath $sevenZip[0].FullName
  & $makensis[0].FullName '/V2' "/DZHANGCAI_OUTPUT=$outputShort" "/DZHANGCAI_INSTALLER_ICO=$iconShort" "/DZHANGCAI_7ZA=$sevenZipShort" "/DZHANGCAI_PROGRAM_PAYLOAD_PART1=$(Get-ShortPath $payloadParts[0])" "/DZHANGCAI_PROGRAM_PAYLOAD_PART2=$(Get-ShortPath $payloadParts[1])" "/DZHANGCAI_PROGRAM_PAYLOAD_PART3=$(Get-ShortPath $payloadParts[2])" "/DZHANGCAI_PROGRAM_PAYLOAD_PART4=$(Get-ShortPath $payloadParts[3])" $nsiShort
  if ($LASTEXITCODE -ne 0) { throw "Program update NSIS build failed with exit code $LASTEXITCODE" }
  if (-not (Test-Path -LiteralPath $compileOutput -PathType Leaf)) { throw "NSIS completed without creating: $compileOutput" }
  Move-Item -LiteralPath $compileOutput -Destination $output
  if (-not (Test-Path -LiteralPath $output -PathType Leaf)) { throw "Program update move completed without creating: $output" }

  $file = Get-Item -LiteralPath $output
  [pscustomobject]@{
    status = 'PASS'
    artifact = $output
    bytes = $file.Length
    megabytes = [math]::Round($file.Length / 1MB, 2)
    sha256 = Get-Sha256 $output
    embeddedPayloadBytes = $payloadBytes
    embeddedPayloadSha256 = Get-Sha256 $payload
    programSourceRoot = $unpackedRoot
    environmentFilesIncluded = $false
    updateRoots = @('resources/app.asar', 'resources/app without node_modules', 'resources/resource-library')
    preservedRoots = @('resources/runtime', 'resources/deepseek-harness', 'resources/app/node_modules', 'data/resource-library')
    environmentReuseCheck = if ($EnvironmentClientRoot) { 'PASS' } else { 'not-supplied; NSIS validates target at install time' }
  } | ConvertTo-Json -Depth 8
}
finally {
  if (Test-Path -LiteralPath $staging) { Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue }
  if (Test-Path -LiteralPath $payload) { Remove-Item -LiteralPath $payload -Force -ErrorAction SilentlyContinue }
  if (Test-Path -LiteralPath $payloadTemp) { Remove-Item -LiteralPath $payloadTemp -Force -ErrorAction SilentlyContinue }
  foreach ($partPath in $payloadParts) {
    if (Test-Path -LiteralPath $partPath) { Remove-Item -LiteralPath $partPath -Force -ErrorAction SilentlyContinue }
  }
}
