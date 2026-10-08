$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'release-paths.ps1')
Assert-NewArtifact (Join-Path $releaseRoot 'win-unpacked')
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'stage-desktop-runtime.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Desktop environment layer staging failed; electron-builder was not started.' }
& (Join-Path $projectRoot '.runtime\node\node.exe') (Join-Path $PSScriptRoot 'stage-desktop-frontend.mjs')
if ($LASTEXITCODE -ne 0) { throw 'Frontend build from current source failed; electron-builder was not started.' }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'package-preflight.ps1') -MainInstaller -RequireHarnessRuntime
if ($LASTEXITCODE -ne 0) { throw 'Package preflight failed; electron-builder was not started.' }

$electronBuilder = Join-Path $projectRoot 'node_modules\.bin\electron-builder.cmd'
$electronBuilderCli = Join-Path $projectRoot 'node_modules\electron-builder\cli.js'
$nodeExecutable = Join-Path $projectRoot '.runtime\node\node.exe'
if (Test-Path -LiteralPath $electronBuilder -PathType Leaf) {
  $builderPrefix = @($electronBuilder)
} elseif ((Test-Path -LiteralPath $electronBuilderCli -PathType Leaf) -and (Test-Path -LiteralPath $nodeExecutable -PathType Leaf)) {
  $builderPrefix = @($nodeExecutable, $electronBuilderCli)
} else {
  throw 'electron-builder is missing. Expected its pinned .cmd shim or node_modules/electron-builder/cli.js with the bundled Node runtime.'
}
Push-Location $projectRoot
try {
  $env:CSC_IDENTITY_AUTO_DISCOVERY = 'false'
  $builderArgs = @('--dir', '--config', 'electron-app/electron-builder.yml', "--config.directories.output=$releaseRoot")
  if ($builderPrefix.Count -gt 1) {
    & $builderPrefix[0] $builderPrefix[1] @builderArgs
  } else {
    & $builderPrefix[0] @builderArgs
  }
  if ($LASTEXITCODE -ne 0) { throw "electron-builder exit code: $LASTEXITCODE" }
} finally {
  Pop-Location
}
