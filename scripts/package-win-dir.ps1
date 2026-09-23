$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'release-paths.ps1')
Assert-NewArtifact (Join-Path $releaseRoot 'win-unpacked')
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'stage-desktop-runtime.ps1')
if ($LASTEXITCODE -ne 0) { throw 'Desktop environment layer staging failed; electron-builder was not started.' }
& powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'package-preflight.ps1') -MainInstaller -RequireHarnessRuntime
if ($LASTEXITCODE -ne 0) { throw 'Package preflight failed; electron-builder was not started.' }

$electronBuilder = Join-Path $projectRoot 'node_modules\.bin\electron-builder.cmd'
if (-not (Test-Path -LiteralPath $electronBuilder)) { throw 'electron-builder is missing.' }
Push-Location $projectRoot
try {
  $env:CSC_IDENTITY_AUTO_DISCOVERY = 'false'
  & $electronBuilder '--dir' '--config' 'electron-app/electron-builder.yml' "--config.directories.output=$releaseRoot"
  if ($LASTEXITCODE -ne 0) { throw "electron-builder exit code: $LASTEXITCODE" }
} finally {
  Pop-Location
}
