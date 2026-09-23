param(
  [string]$OutputRoot = ''
)

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $PSScriptRoot 'release-paths.ps1')

$environmentBaselineVersionFile = Join-Path $projectRoot 'packaging\environment-baseline-version.txt'
if (-not (Test-Path -LiteralPath $environmentBaselineVersionFile -PathType Leaf)) {
  throw "Missing environment baseline version file: $environmentBaselineVersionFile"
}
$environmentBaselineVersion = (Get-Content -LiteralPath $environmentBaselineVersionFile -Raw -Encoding UTF8).Trim()
if ($environmentBaselineVersion -notmatch '^\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?$') {
  throw "Invalid environment baseline version: $environmentBaselineVersion"
}

if (-not $OutputRoot) {
  $OutputRoot = Join-Path $projectRoot 'packaging\staging\desktop-runtime'
}

$stageRoot = [System.IO.Path]::GetFullPath($OutputRoot).TrimEnd('\')
$projectFull = [System.IO.Path]::GetFullPath($projectRoot).TrimEnd('\')
$allowedStageRoot = Join-Path $projectFull 'packaging\staging'
$allowedStagePrefix = $allowedStageRoot.TrimEnd('\') + '\'
if ($stageRoot -ne $allowedStageRoot -and -not $stageRoot.StartsWith($allowedStagePrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
  throw "Refusing to create runtime staging outside packaging/staging: $stageRoot"
}

function Require-Source([string]$relativePath, [string]$label) {
  $source = Join-Path $projectRoot $relativePath
  if (-not (Test-Path -LiteralPath $source)) { throw "Missing $label`: $relativePath" }
  return (Resolve-Path -LiteralPath $source).Path.TrimEnd('\')
}

function Invoke-Robocopy([string]$source, [string]$destination, [string[]]$excludeDirectories = @(), [string[]]$excludeFiles = @()) {
  New-Item -ItemType Directory -Path $destination -Force | Out-Null
  $arguments = @(
    $source,
    $destination,
    '/E',
    '/COPY:DAT',
    '/DCOPY:DAT',
    '/R:1',
    '/W:1',
    '/XJ',
    '/NFL',
    '/NDL',
    '/NJH',
    '/NJS',
    '/NP'
  )
  if ($excludeFiles.Count -gt 0) { $arguments += @('/XF') + $excludeFiles }
  if ($excludeDirectories.Count -gt 0) { $arguments += @('/XD') + $excludeDirectories }
  & robocopy.exe @arguments | Out-Null
  $code = $LASTEXITCODE
  if ($code -gt 7) { throw "Robocopy failed ($code): $source -> $destination" }
}

function Remove-RuntimeJunk([string]$root) {
  $filePatterns = @(
    '(?i)\.map$',
    '(?i)\.d\.(ts|mts|cts)$',
    '(?i)\.(ts|mts|cts|tsx)$',
    '(?i)^(README|LICENSE|LICENCE|CHANGELOG|CONTRIBUTING|NOTICE)(\.|$)',
    '(?i)^(pnpm-lock|package-lock|yarn\.lock)$',
    '(?i)^\.npmignore$'
  )
  $files = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force -ErrorAction SilentlyContinue)
  foreach ($file in $files) {
    if ($filePatterns | Where-Object { $file.Name -match $_ }) {
      Remove-Item -LiteralPath $file.FullName -Force
    }
  }

  $directoryNames = @(
    '.cache', '.vite', '.turbo', '.git', 'coverage',
    'test', 'tests', '__tests__', 'examples', 'example',
    'bench', 'benchmarks'
  )
  $directories = @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $directoryNames -contains $_.Name } |
    Sort-Object FullName -Descending)
  foreach ($directory in $directories) {
    if (Test-Path -LiteralPath $directory.FullName -PathType Container) {
      Remove-Item -LiteralPath $directory.FullName -Recurse -Force
    }
  }

  $rootPackageStore = Join-Path $root '.pnpm'
  if (Test-Path -LiteralPath $rootPackageStore -PathType Container) {
    Remove-Item -LiteralPath $rootPackageStore -Recurse -Force
  }
  foreach ($rootFileName in @('.modules.yaml', '.package-map.json')) {
    $rootFile = Join-Path $root $rootFileName
    if (Test-Path -LiteralPath $rootFile -PathType Leaf) {
      Remove-Item -LiteralPath $rootFile -Force
    }
  }
}

function Remove-PythonJunk([string]$root) {
  $files = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Extension -in @('.pyc', '.pyo') })
  foreach ($file in $files) { Remove-Item -LiteralPath $file.FullName -Force }

  $directories = @(Get-ChildItem -LiteralPath $root -Recurse -Directory -Force -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -eq '__pycache__' } |
    Sort-Object FullName -Descending)
  foreach ($directory in $directories) {
    if (Test-Path -LiteralPath $directory.FullName -PathType Container) {
      Remove-Item -LiteralPath $directory.FullName -Recurse -Force
    }
  }

  $sitePackages = Join-Path $root 'Lib\site-packages'
  if (Test-Path -LiteralPath $sitePackages -PathType Container) {
    $removeNames = @('pip', 'setuptools', 'wheel', '_distutils_hack')
    $removeEntries = @(Get-ChildItem -LiteralPath $sitePackages -Force |
      Where-Object {
        ($removeNames -contains $_.BaseName) -or
        ($_.Name -match '^(pip|setuptools|wheel)-.*\.dist-info$')
      })
    foreach ($entry in $removeEntries) {
      Remove-Item -LiteralPath $entry.FullName -Recurse -Force
    }
  }
}

function Get-TreeStats([string]$root) {
  $files = @(Get-ChildItem -LiteralPath $root -Recurse -File -Force -ErrorAction SilentlyContinue)
  $sum = ($files | Measure-Object -Property Length -Sum).Sum
  if ($null -eq $sum) { $sum = 0 }
  return [ordered]@{
    files = $files.Count
    bytes = [int64]$sum
  }
}

function Write-EnvironmentVersionIni([string]$root, [string]$baselineVersion, [string]$packageVersion) {
  $ini = @"
[Environment]
Schema=ZHANGCAI_DESKTOP_ENVIRONMENT_LAYER_V1
BaselineVersion=$baselineVersion
PackageVersion=$packageVersion
HarnessVersion=0.1.2-rc.1
NodeVersion=24.19.0
PythonVersion=3.12.14
VinextVersion=1.0.0-beta.5
"@.TrimStart()
  $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
  [System.IO.File]::WriteAllText((Join-Path $root 'environment-version.ini'), $ini, $utf8NoBom)
}

if (Test-Path -LiteralPath $stageRoot) {
  $existingManifestPath = Join-Path $stageRoot 'manifest.json'
  $existingManifest = $null
  try {
    if (Test-Path -LiteralPath $existingManifestPath -PathType Leaf) {
      $existingManifest = Get-Content -LiteralPath $existingManifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    }
  } catch {
    $existingManifest = $null
  }
  $existingRuntimeComplete = @(
    (Join-Path $stageRoot 'app-node-modules\vinext\dist\cli.js'),
    (Join-Path $stageRoot 'deepseek-harness\lib\bin.js'),
    (Join-Path $stageRoot 'deepseek-harness\node_modules\yaml\dist\doc\directives.js'),
    (Join-Path $stageRoot 'python\python.exe'),
    (Join-Path $stageRoot 'manifest.json')
  ) | Where-Object { -not (Test-Path -LiteralPath $_) }
  if ($existingManifest -and
      [string]$existingManifest.baselineVersion -eq $environmentBaselineVersion -and
      $existingRuntimeComplete.Count -eq 0) {
    $existingManifest.packageVersion = $releaseVersion
    $existingManifest.generatedAt = (Get-Date).ToUniversalTime().ToString('o')
    $utf8NoBom = New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($existingManifestPath, ($existingManifest | ConvertTo-Json -Depth 8), $utf8NoBom)
    Write-Output "Reusable desktop environment layer already matches baseline $environmentBaselineVersion; keeping existing files."
    Write-EnvironmentVersionIni $stageRoot $environmentBaselineVersion $releaseVersion
    [pscustomobject]@{
      status = 'REUSED'
      stagingRoot = $stageRoot
      packageVersion = $releaseVersion
      baselineVersion = $environmentBaselineVersion
      manifest = $existingManifestPath
      components = $existingManifest.components
    } | ConvertTo-Json -Depth 8
    return
  }
  $quarantine = Join-Path $projectRoot ("dist-installer\quarantine\runtime-staging-{0}" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
  New-Item -ItemType Directory -Path (Split-Path -Parent $quarantine) -Force | Out-Null
  Move-Item -LiteralPath $stageRoot -Destination $quarantine
}
New-Item -ItemType Directory -Path $stageRoot -Force | Out-Null

$runtimeNodeModules = Require-Source 'packaging\runtime-node-modules' 'production Node module tree'
$harnessVendor = Require-Source 'packaging\vendor\deepseek-harness' 'DeepSeek Harness vendor tree'
$bundledPython = Require-Source '.runtime\python' 'bundled Python runtime'

$appNodeModulesStage = Join-Path $stageRoot 'app-node-modules'
$harnessStage = Join-Path $stageRoot 'deepseek-harness'
$pythonStage = Join-Path $stageRoot 'python'

Write-Output 'Staging production Node module tree...'
Invoke-Robocopy $runtimeNodeModules $appNodeModulesStage @() @('*.map', '*.d.ts', '*.d.mts', '*.d.cts', '*.ts', '*.mts', '*.cts', '*.tsx', 'README*', 'LICENSE*', 'LICENCE*', 'CHANGELOG*', 'CONTRIBUTING*', 'NOTICE*', 'pnpm-lock.yaml', 'package-lock.json', 'yarn.lock', '.npmignore')
Remove-RuntimeJunk $appNodeModulesStage

Write-Output 'Staging DeepSeek Harness runtime...'
New-Item -ItemType Directory -Path $harnessStage -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $harnessVendor 'package.json') -Destination (Join-Path $harnessStage 'package.json') -Force
Invoke-Robocopy (Join-Path $harnessVendor 'lib') (Join-Path $harnessStage 'lib') @() @('*.map', '*.d.ts', '*.d.mts', '*.d.cts', '*.ts', '*.mts', '*.cts', '*.tsx', 'README*', 'LICENSE*', 'LICENCE*')
Invoke-Robocopy (Join-Path $harnessVendor 'node_modules') (Join-Path $harnessStage 'node_modules') @() @('*.map', '*.d.ts', '*.d.mts', '*.d.cts', '*.ts', '*.mts', '*.cts', '*.tsx', 'README*', 'LICENSE*', 'LICENCE*', 'CHANGELOG*', 'CONTRIBUTING*', 'NOTICE*', 'pnpm-lock.yaml', 'package-lock.json', 'yarn.lock', '.npmignore')
Remove-RuntimeJunk (Join-Path $harnessStage 'node_modules')

Write-Output 'Staging Python runtime without installer-only components...'
Invoke-Robocopy $bundledPython $pythonStage @(
  (Join-Path $bundledPython 'include'),
  (Join-Path $bundledPython 'libs'),
  (Join-Path $bundledPython 'tcl'),
  (Join-Path $bundledPython 'Tools'),
  (Join-Path $bundledPython 'idlelib'),
  (Join-Path $bundledPython 'Lib\test'),
  (Join-Path $bundledPython 'Lib\ensurepip'),
  (Join-Path $bundledPython 'Scripts')
) @('*.pyc', '*.pyo')
Remove-PythonJunk $pythonStage

$manifest = [ordered]@{
  schema = 'ZHANGCAI_DESKTOP_ENVIRONMENT_LAYER_V1'
  packageVersion = $releaseVersion
  baselineVersion = $environmentBaselineVersion
  harnessVersion = '0.1.2-rc.1'
  reusePolicy = 'program-updates-must-not-reinstall-or-overwrite-this-layer-when-runtime-manifest-matches'
  sourcePolicy = 'derived-from-pinned-project-runtime-sources; build-only-staging-is-not-user-data'
  prunePolicy = @(
    'remove JavaScript source maps, TypeScript sources and declaration files'
    'remove package documentation, examples, tests and package-manager metadata'
    'remove Python headers, static libraries, Tcl/Tk, tests, pip, setuptools, wheel and bytecode caches'
  )
  components = [ordered]@{
    appNodeModules = Get-TreeStats $appNodeModulesStage
    deepseekHarness = Get-TreeStats $harnessStage
    python = Get-TreeStats $pythonStage
  }
  generatedAt = (Get-Date).ToUniversalTime().ToString('o')
}
$manifestPath = Join-Path $stageRoot 'manifest.json'
$utf8NoBom = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllText($manifestPath, ($manifest | ConvertTo-Json -Depth 8), $utf8NoBom)
Write-EnvironmentVersionIni $stageRoot $environmentBaselineVersion $releaseVersion

[pscustomobject]@{
  status = 'PASS'
  stagingRoot = $stageRoot
  packageVersion = $releaseVersion
  baselineVersion = $environmentBaselineVersion
  manifest = $manifestPath
  components = $manifest.components
} | ConvertTo-Json -Depth 8
