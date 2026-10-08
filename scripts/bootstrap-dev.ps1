param([switch]$SkipInstall, [switch]$FreshDependencyStore)
$ErrorActionPreference = 'Stop'
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$project = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if ([Environment]::OSVersion.Platform -ne 'Win32NT' -or -not [Environment]::Is64BitOperatingSystem) { throw 'This desktop toolchain requires Windows x64.' }
$manifest = Get-Content -LiteralPath (Join-Path $project 'development-assets/manifest.json') -Raw -Encoding UTF8 | ConvertFrom-Json
if (@($manifest.pythonDevWheels).Count -ne 6) { throw 'The locked development wheel manifest must contain six wheels.' }
function Asset-Path($asset) {
  $file = Join-Path $project $asset.path
  if (-not (Test-Path -LiteralPath $file -PathType Leaf)) { throw "Missing $($asset.path). Run git lfs pull first." }
  if ((Get-Item -LiteralPath $file).Length -ne $asset.bytes -or (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() -ne $asset.sha256) { throw "Incomplete or changed LFS asset: $($asset.path). Run git lfs pull." }
  return $file
}
$installer = Asset-Path $manifest.installer
$tools = Asset-Path $manifest.tools
$receiptPath = Join-Path $project '.runtime/development-receipt.json'
$required = @('.runtime/node/node.exe','.runtime/python/python.exe','.runtime/tools/pnpm/bin/pnpm.mjs','.runtime/bin/pnpm.cmd','packaging/staging/desktop-runtime/manifest.json','packaging/vendor/deepseek-harness/lib/bin.js','packaging/runtime-node-modules/vinext/dist/cli.js')
$reuse = $false
if (Test-Path -LiteralPath $receiptPath) {
  $receipt = Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
  $reuse = $receipt.installerSha256 -eq $manifest.installer.sha256 -and $receipt.toolsSha256 -eq $manifest.tools.sha256 -and @($required | Where-Object { -not (Test-Path -LiteralPath (Join-Path $project $_)) }).Count -eq 0
  if (-not $reuse) { throw 'The prepared development runtime differs or is incomplete. Preserve it before preparing a separate clean checkout.' }
}
if (-not $reuse) {
  foreach ($path in @('.runtime/node/node.exe','packaging/staging/desktop-runtime/manifest.json')) {
    if (Test-Path -LiteralPath (Join-Path $project $path)) { throw "Existing runtime without a development receipt: $path. Prepare a clean checkout." }
  }
  $temp = Join-Path $project ('.bootstrap-extract-' + [guid]::NewGuid().ToString('N'))
  New-Item -ItemType Directory -Path $temp -Force | Out-Null
  try {
    $toolRoot = Join-Path $project '.runtime/tools'
    Expand-Archive -LiteralPath $tools -DestinationPath $toolRoot
    $sevenZip = Join-Path $toolRoot '7zip/bin/7za.exe'
    & $sevenZip x $installer "-o$temp" '-y' '-bso0' '-bsp0' 'resources/runtime/*' 'resources/deepseek-harness/*' 'resources/app/node_modules/*'
    if ($LASTEXITCODE -ne 0) { throw "Installer runtime extraction failed: $LASTEXITCODE" }
    $resources = Join-Path $temp 'resources'
    $stage = Join-Path $project 'packaging/staging/desktop-runtime'
    New-Item -ItemType Directory -Path $stage,(Join-Path $project '.runtime/node'),(Join-Path $project 'packaging/vendor'),(Join-Path $project '.runtime/bin') -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $resources 'runtime/node/node.exe') -Destination (Join-Path $project '.runtime/node/node.exe')
    Copy-Item -LiteralPath (Join-Path $resources 'runtime/python') -Destination (Join-Path $project '.runtime/python') -Recurse
    Copy-Item -LiteralPath (Join-Path $resources 'runtime/python') -Destination (Join-Path $stage 'python') -Recurse
    Copy-Item -LiteralPath (Join-Path $resources 'deepseek-harness') -Destination (Join-Path $stage 'deepseek-harness') -Recurse
    Copy-Item -LiteralPath (Join-Path $resources 'deepseek-harness') -Destination (Join-Path $project 'packaging/vendor/deepseek-harness') -Recurse
    Copy-Item -LiteralPath (Join-Path $resources 'app/node_modules') -Destination (Join-Path $stage 'app-node-modules') -Recurse
    Copy-Item -LiteralPath (Join-Path $resources 'app/node_modules') -Destination (Join-Path $project 'packaging/runtime-node-modules') -Recurse
    Copy-Item -LiteralPath (Join-Path $resources 'runtime/environment-manifest.json') -Destination (Join-Path $stage 'manifest.json')
    Copy-Item -LiteralPath (Join-Path $resources 'runtime/environment-version.ini') -Destination (Join-Path $stage 'environment-version.ini')
    Copy-Item -LiteralPath (Join-Path $toolRoot 'python/Lib/ensurepip') -Destination (Join-Path $project '.runtime/python/Lib/ensurepip') -Recurse
    # The original pruned environment retained setuptools' startup .pth but
    # not _distutils_hack. Disable that orphaned hook, retaining it for audit.
    foreach ($pythonRoot in @((Join-Path $project '.runtime/python'),(Join-Path $stage 'python'))) {
      $hook = Join-Path $pythonRoot 'Lib/site-packages/distutils-precedence.pth'
      if ((Test-Path -LiteralPath $hook) -and -not (Test-Path -LiteralPath (Join-Path $pythonRoot 'Lib/site-packages/_distutils_hack'))) {
        Rename-Item -LiteralPath $hook -NewName 'distutils-precedence.pth.disabled'
      }
    }
    $shim = "@echo off`r`nsetlocal`r`n`"%~dp0..\node\node.exe`" `"%~dp0..\tools\pnpm\bin\pnpm.mjs`" %*`r`nexit /b %ERRORLEVEL%`r`n"
    [IO.File]::WriteAllText((Join-Path $project '.runtime/bin/pnpm.cmd'), $shim, [Text.UTF8Encoding]::new($false))
    & (Join-Path $project '.runtime/python/python.exe') -m ensurepip --upgrade
    if ($LASTEXITCODE -ne 0) { throw 'Developer Python pip preparation failed.' }
    [IO.File]::WriteAllText($receiptPath, (@{ installerSha256=$manifest.installer.sha256; toolsSha256=$manifest.tools.sha256; baseline=$manifest.environmentBaseline } | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
  } finally {
    $resolvedTemp = [IO.Path]::GetFullPath($temp)
    if ($resolvedTemp.StartsWith($project + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -and (Split-Path $resolvedTemp -Leaf) -like '.bootstrap-extract-*') { Remove-Item -LiteralPath $resolvedTemp -Recurse -Force }
  }
}
# Also repair the audited orphaned hook on a receipt-verified older preparation.
foreach ($pythonRoot in @((Join-Path $project '.runtime/python'),(Join-Path $project 'packaging/staging/desktop-runtime/python'))) {
  $hook = Join-Path $pythonRoot 'Lib/site-packages/distutils-precedence.pth'
  if ((Test-Path -LiteralPath $hook) -and -not (Test-Path -LiteralPath (Join-Path $pythonRoot 'Lib/site-packages/_distutils_hack'))) {
    Rename-Item -LiteralPath $hook -NewName 'distutils-precedence.pth.disabled'
  }
}
& (Join-Path $project '.runtime/node/node.exe') --version
& (Join-Path $project '.runtime/python/python.exe') --version
if (-not $SkipInstall) {
  if ($FreshDependencyStore -and (Test-Path -LiteralPath (Join-Path $project 'node_modules'))) { throw 'FreshDependencyStore is only for a clean checkout without node_modules.' }
  foreach ($wheel in $manifest.pythonDevWheels) { $null = Asset-Path $wheel }
  & (Join-Path $project '.runtime/python/python.exe') -m pip install --disable-pip-version-check --no-index --find-links (Join-Path $project 'development-assets/python-dev-wheels') --require-hashes -r (Join-Path $project 'requirements-dev-lock.txt')
  if ($LASTEXITCODE -ne 0) { throw 'Locked Python development dependency installation failed.' }
  $installArgs = @('install','--frozen-lockfile')
  if ($FreshDependencyStore) { $installArgs += @('--store-dir',(Join-Path $project '.runtime/pnpm-store')) }
  & (Join-Path $PSScriptRoot 'pnpm.ps1') @installArgs
  if ($LASTEXITCODE -ne 0) { throw 'Frozen dependency installation failed.' }
}
Write-Output 'Development runtime prepared. Use scripts/pnpm.ps1 for project commands.'
