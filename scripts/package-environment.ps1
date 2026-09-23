param(
  [string]$OutputDirectory = ''
)

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'release-paths.ps1')
$outputRoot = if ($OutputDirectory) {
  [System.IO.Path]::GetFullPath((Join-Path $projectRoot $OutputDirectory))
} else { $releaseRoot }
New-Item -ItemType Directory -Path $outputRoot -Force | Out-Null

$baselineFile = Join-Path $projectRoot 'packaging\environment-baseline-version.txt'
$baselineVersion = (Get-Content -LiteralPath $baselineFile -Raw -Encoding UTF8).Trim()
if ($baselineVersion -notmatch '^\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?$') { throw "Invalid environment baseline version: $baselineVersion" }

$productName = -join @([char]0x638C, [char]0x8D22, [char]0x684C, [char]0x9762, [char]0x7AEF)
$environmentLabel = -join @([char]0x8FD0, [char]0x884C, [char]0x73AF, [char]0x5883)
$uninstallLabel = -join @([char]0x8FD0, [char]0x884C, [char]0x73AF, [char]0x5883, [char]0x5378, [char]0x8F7D)
$environmentOutput = Join-Path $outputRoot ($productName + '-' + $environmentLabel + '-' + $releaseVersion + '-x64.exe')
$uninstallerOutput = Join-Path $outputRoot ($productName + '-' + $uninstallLabel + '-' + $releaseVersion + '-x64.exe')
Assert-NewArtifact $environmentOutput
Assert-NewArtifact $uninstallerOutput

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'stop-packaging-processes.ps1') -WorkspaceRoot $projectRoot
if ($LASTEXITCODE -ne 0) { throw 'Failed to stop packaging-conflicting project processes.' }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'stage-desktop-runtime.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Desktop environment layer staging failed.' }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'package-preflight.ps1') -RequireHarnessRuntime
if ($LASTEXITCODE -ne 0) { throw 'Package preflight failed.' }

function Get-ShortPath([string]$path) {
  $fso = New-Object -ComObject Scripting.FileSystemObject
  if (Test-Path -LiteralPath $path -PathType Container) { return $fso.GetFolder($path).ShortPath }
  if (Test-Path -LiteralPath $path -PathType Leaf) { return $fso.GetFile($path).ShortPath }
  $parent = Split-Path -Parent $path
  if (-not (Test-Path -LiteralPath $parent -PathType Container)) { throw "Missing path for 8.3 conversion: $path" }
  return (Join-Path $fso.GetFolder($parent).ShortPath (Split-Path -Leaf $path))
}

function Invoke-Robocopy([string]$source, [string]$destination) {
  New-Item -ItemType Directory -Path $destination -Force | Out-Null
  & robocopy.exe $source $destination /E /COPY:DAT /DCOPY:DAT /R:1 /W:1 /XJ /NFL /NDL /NJH /NJS /NP | Out-Null
  if ($LASTEXITCODE -gt 7) { throw "Robocopy failed ($LASTEXITCODE): $source -> $destination" }
}

function Get-Sha256([string]$filePath) {
  $algorithm = [System.Security.Cryptography.SHA256]::Create()
  $stream = [System.IO.File]::OpenRead($filePath)
  try { return ([System.BitConverter]::ToString($algorithm.ComputeHash($stream)).Replace('-', '')).ToLowerInvariant() }
  finally { $stream.Dispose(); $algorithm.Dispose() }
}

$stageRoot = Join-Path $projectRoot 'packaging\staging\desktop-runtime'
$environmentPayloadRoot = Join-Path $releaseRoot ('.environment-package-staging-' + [guid]::NewGuid().ToString('N'))
$payload = Join-Path $outputRoot "zhangcai-environment-$releaseVersion.7z"
$payloadTemp = Join-Path $outputRoot "zhangcai-environment-$releaseVersion.tmp.7z"
$payloadParts = @()
$compileInstallerOutput = Join-Path $outputRoot "environment-installer-$releaseVersion-x64.exe"
$compileUninstallerOutput = Join-Path $outputRoot "environment-uninstaller-$releaseVersion-x64.exe"

$sevenZip = @(Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'electron-builder\Cache') -Recurse -Filter '7za.exe' -File -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1)
if (-not $sevenZip) { throw '7za.exe was not found in the electron-builder cache.' }
$makensis = @(Get-ChildItem -LiteralPath (Join-Path $env:LOCALAPPDATA 'electron-builder\Cache\nsis') -Recurse -Filter 'makensis.exe' -File -ErrorAction SilentlyContinue | Sort-Object FullName -Descending | Select-Object -First 1)
if (-not $makensis) { throw 'makensis.exe was not found in the electron-builder NSIS cache.' }
$icon = (Resolve-Path -LiteralPath (Join-Path $projectRoot 'electron-app\resources\installer-icon.ico')).Path
$installerNsi = (Resolve-Path -LiteralPath (Join-Path $projectRoot 'electron-app\nsis\environment-installer.nsi')).Path
$uninstallerNsi = (Resolve-Path -LiteralPath (Join-Path $projectRoot 'electron-app\nsis\environment-uninstaller.nsi')).Path

try {
  $payloadResources = Join-Path $environmentPayloadRoot 'resources'
  New-Item -ItemType Directory -Path $payloadResources -Force | Out-Null
  Invoke-Robocopy (Join-Path $stageRoot 'app-node-modules') (Join-Path $payloadResources 'app\node_modules')
  Invoke-Robocopy (Join-Path $stageRoot 'deepseek-harness') (Join-Path $payloadResources 'deepseek-harness')
  Invoke-Robocopy (Join-Path $stageRoot 'python') (Join-Path $payloadResources 'runtime\python')
  New-Item -ItemType Directory -Path (Join-Path $payloadResources 'runtime\node') -Force | Out-Null
  Copy-Item -LiteralPath (Join-Path $projectRoot '.runtime\node\node.exe') -Destination (Join-Path $payloadResources 'runtime\node\node.exe') -Force
  Copy-Item -LiteralPath (Join-Path $stageRoot 'manifest.json') -Destination (Join-Path $payloadResources 'runtime\environment-manifest.json') -Force
  Copy-Item -LiteralPath (Join-Path $stageRoot 'environment-version.ini') -Destination (Join-Path $payloadResources 'runtime\environment-version.ini') -Force

  $stagingShort = Get-ShortPath $environmentPayloadRoot
  $payloadTempShort = Get-ShortPath $payloadTemp
  Write-Output "Creating environment-only payload: $payloadTemp"
  Push-Location $stagingShort
  try {
    & $sevenZip[0].FullName 'a' $payloadTempShort 'resources' '-mx=1' '-mmt=on' '-m0=lzma2' '-md=8m' '-ms=on' '-y'
    if ($LASTEXITCODE -ne 0) { throw "Environment payload build failed with exit code $LASTEXITCODE" }
  } finally { Pop-Location }
  Move-Item -LiteralPath $payloadTemp -Destination $payload -Force
  & $sevenZip[0].FullName 't' (Get-ShortPath $payload) '-y'
  if ($LASTEXITCODE -ne 0) { throw "Environment payload integrity test failed with exit code $LASTEXITCODE" }

  $payloadBytes = (Get-Item -LiteralPath $payload).Length
  $partSize = [int64][math]::Ceiling($payloadBytes / 4)
  $input = [System.IO.File]::OpenRead($payload)
  try {
    $buffer = New-Object byte[] (4MB)
    for ($index = 1; $index -le 4; $index++) {
      $partPath = Join-Path $outputRoot ("penv{0}.bin" -f $index)
      $outputStream = [System.IO.File]::Open($partPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
      try {
        $remaining = [int64][math]::Min($partSize, $payloadBytes - $input.Position)
        while ($remaining -gt 0) {
          $requested = [int][math]::Min($buffer.Length, $remaining)
          $read = $input.Read($buffer, 0, $requested)
          if ($read -le 0) { throw "Unexpected end of environment payload at part $index." }
          $outputStream.Write($buffer, 0, $read)
          $remaining -= $read
        }
      } finally { $outputStream.Dispose() }
      $payloadParts += $partPath
    }
  } finally { $input.Dispose() }

  $iconShort = Get-ShortPath $icon
  $sevenZipShort = Get-ShortPath $sevenZip[0].FullName
  $installerNsiShort = Get-ShortPath $installerNsi
  $uninstallerNsiShort = Get-ShortPath $uninstallerNsi
  $compileInstallerShort = Get-ShortPath $compileInstallerOutput
  $compileUninstallerShort = Get-ShortPath $compileUninstallerOutput
  & $makensis[0].FullName '/V2' "/DZHANGCAI_OUTPUT=$compileInstallerShort" "/DZHANGCAI_INSTALLER_ICO=$iconShort" "/DZHANGCAI_7ZA=$sevenZipShort" "/DZHANGCAI_ENV_BASELINE_VERSION=$baselineVersion" "/DZHANGCAI_ENV_PAYLOAD_PART1=$(Get-ShortPath $payloadParts[0])" "/DZHANGCAI_ENV_PAYLOAD_PART2=$(Get-ShortPath $payloadParts[1])" "/DZHANGCAI_ENV_PAYLOAD_PART3=$(Get-ShortPath $payloadParts[2])" "/DZHANGCAI_ENV_PAYLOAD_PART4=$(Get-ShortPath $payloadParts[3])" $installerNsiShort
  if ($LASTEXITCODE -ne 0) { throw "Environment installer NSIS build failed with exit code $LASTEXITCODE" }
  if (-not (Test-Path -LiteralPath $compileInstallerOutput -PathType Leaf)) { throw "NSIS completed without creating: $compileInstallerOutput" }
  Move-Item -LiteralPath $compileInstallerOutput -Destination $environmentOutput

  & $makensis[0].FullName '/V2' "/DZHANGCAI_OUTPUT=$compileUninstallerShort" "/DZHANGCAI_INSTALLER_ICO=$iconShort" "/DZHANGCAI_ENV_BASELINE_VERSION=$baselineVersion" $uninstallerNsiShort
  if ($LASTEXITCODE -ne 0) { throw "Environment uninstaller NSIS build failed with exit code $LASTEXITCODE" }
  if (-not (Test-Path -LiteralPath $compileUninstallerOutput -PathType Leaf)) { throw "NSIS completed without creating: $compileUninstallerOutput" }
  Move-Item -LiteralPath $compileUninstallerOutput -Destination $uninstallerOutput

  [pscustomobject]@{
    status = 'PASS'
    packageVersion = $releaseVersion
    environmentBaselineVersion = $baselineVersion
    environmentInstaller = $environmentOutput
    environmentInstallerBytes = (Get-Item -LiteralPath $environmentOutput).Length
    environmentInstallerSha256 = Get-Sha256 $environmentOutput
    environmentUninstaller = $uninstallerOutput
    environmentUninstallerBytes = (Get-Item -LiteralPath $uninstallerOutput).Length
    environmentPayloadBytes = $payloadBytes
    environmentPayloadSha256 = Get-Sha256 $payload
    containsMainProgram = $false
    installedRoots = @('resources/runtime', 'resources/deepseek-harness', 'resources/app/node_modules')
    preservedRoots = @('resources/app.asar', 'resources/app without node_modules', 'data/resource-library')
    detectedVersions = @{ node = '24.19.0'; python = '3.12.14'; harness = '0.1.2-rc.1'; vinext = '1.0.0-beta.5' }
  } | ConvertTo-Json -Depth 8
}
finally {
  if (Test-Path -LiteralPath $environmentPayloadRoot) { Remove-Item -LiteralPath $environmentPayloadRoot -Recurse -Force -ErrorAction SilentlyContinue }
  if (Test-Path -LiteralPath $payload) { Remove-Item -LiteralPath $payload -Force -ErrorAction SilentlyContinue }
  if (Test-Path -LiteralPath $payloadTemp) { Remove-Item -LiteralPath $payloadTemp -Force -ErrorAction SilentlyContinue }
  foreach ($partPath in $payloadParts) {
    if (Test-Path -LiteralPath $partPath) { Remove-Item -LiteralPath $partPath -Force -ErrorAction SilentlyContinue }
  }
}
