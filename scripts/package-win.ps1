$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'release-paths.ps1')
Assert-NewArtifact (Join-Path $releaseRoot "掌财桌面端-$releaseVersion-x64.exe")
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'stop-packaging-processes.ps1') -WorkspaceRoot $projectRoot
if ($LASTEXITCODE -ne 0) { throw 'Failed to stop packaging-conflicting project processes.' }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'stage-desktop-runtime.ps1')
if ($LASTEXITCODE -ne 0) {
  throw 'Desktop environment layer staging failed; electron-builder was not started.'
}
& (Join-Path $projectRoot '.runtime\node\node.exe') (Join-Path $PSScriptRoot 'stage-recovered-frontend.mjs')
if ($LASTEXITCODE -ne 0) {
  throw 'Verified recovered frontend/formula staging failed; electron-builder was not started.'
}
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'package-preflight.ps1') -MainInstaller -RequireHarnessRuntime
if ($LASTEXITCODE -ne 0) {
  throw 'Package preflight failed; electron-builder was not started.'
}
$electronBuilder = Join-Path $projectRoot 'node_modules\.bin\electron-builder.cmd'
$electronBuilderCli = Join-Path $projectRoot 'node_modules\electron-builder\cli.js'
$nodeExecutable = Join-Path $projectRoot '.runtime\node\node.exe'
$useNodeCli = $false
if (-not (Test-Path -LiteralPath $electronBuilder -PathType Leaf)) {
  if ((Test-Path -LiteralPath $electronBuilderCli -PathType Leaf) -and (Test-Path -LiteralPath $nodeExecutable -PathType Leaf)) {
    $electronBuilder = $electronBuilderCli
    $useNodeCli = $true
  } else {
    throw 'electron-builder is missing. Expected its pinned .cmd shim or node_modules/electron-builder/cli.js with the bundled Node runtime.'
  }
}

Push-Location $projectRoot
try {
  $oldCompressionLevel = $env:ELECTRON_BUILDER_COMPRESSION_LEVEL
  # The desktop runtime already consists mainly of compressed Python wheels,
  # Electron archives and native binaries.  Store mode avoids spending tens of
  # minutes recompressing them, while keeping the installer self-contained.
  $env:ELECTRON_BUILDER_COMPRESSION_LEVEL = '0'
  $builderArgs = @('-ElectronBuilder', $electronBuilder, '-ConfigPath', 'electron-app/electron-builder.yml', '-OutputDirectory', $releaseRoot)
  if ($useNodeCli) { $builderArgs += @('-NodeExecutable', $nodeExecutable) }
  & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'build-electron-with-visible-details.ps1') @builderArgs
  if ($LASTEXITCODE -ne 0) { throw "electron-builder exit code: $LASTEXITCODE" }
} finally {
  $env:ELECTRON_BUILDER_COMPRESSION_LEVEL = $oldCompressionLevel
  Pop-Location
}
