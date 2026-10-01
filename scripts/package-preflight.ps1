param(
  [switch]$RequireHarnessRuntime,
  [switch]$MainInstaller,
  [switch]$CheckRunning
)

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$packageFile = Join-Path $projectRoot 'package.json'
$package = Get-Content -LiteralPath $packageFile -Raw | ConvertFrom-Json
$siteBuildDist = Join-Path 'packaging\staging' ("site-build-$($package.version)\dist")
$errors = New-Object 'System.Collections.Generic.List[string]'
$warnings = New-Object 'System.Collections.Generic.List[string]'
$mainInstallerPolicyPath = Join-Path $projectRoot 'packaging\main-installer-policy.json'
$mainInstallerPolicy = $null

if (-not (Test-Path -LiteralPath $mainInstallerPolicyPath -PathType Leaf)) {
  $errors.Add('Missing main installer packaging policy: packaging\main-installer-policy.json')
}
else {
  try {
    $mainInstallerPolicy = Get-Content -LiteralPath $mainInstallerPolicyPath -Raw -Encoding UTF8 | ConvertFrom-Json
  }
  catch {
    $errors.Add("Invalid main installer packaging policy: $($_.Exception.Message)")
  }
}

if ($MainInstaller -and $null -ne $mainInstallerPolicy) {
  if ($mainInstallerPolicy.mainInstaller.dataPackInput -ne 'forbidden') {
    $errors.Add('Main installer policy must forbid the independent data-pack as a build input.')
  }
  if ($mainInstallerPolicy.mainInstaller.dataPackRequiredBeforeBuild -ne $false) {
    $errors.Add('Main installer policy must not require a data-pack artifact before build.')
  }
  if ($mainInstallerPolicy.baselineRuntime.embeddedInMainInstaller -ne $true) {
    $errors.Add('Main installer policy must embed the baseline runtime.')
  }
  if ($mainInstallerPolicy.baselineRuntime.reusedByProgramUpdates -ne $true) {
    $errors.Add('Main installer policy must mark the baseline runtime as reusable by program updates.')
  }
}

function Require-Path([string]$relativePath, [string]$label) {
  $target = Join-Path $projectRoot $relativePath
  if (-not (Test-Path -LiteralPath $target)) {
    $errors.Add("Missing $label`: $relativePath")
  }
}

Require-Path 'agent-server.mjs' 'bridge entry'
Require-Path (Join-Path $siteBuildDist 'client') 'Vinext client build'
Require-Path (Join-Path $siteBuildDist 'server') 'Vinext server build'
Require-Path 'harness-skills' 'skill directory'
Require-Path 'skill-archives' 'Skill14 source archive directory'
Require-Path 'scripts\verify_skill14_archives.py' 'Skill14 archive release verifier'
Require-Path 'scripts\verify_stock_detail_skills.py' 'stock-detail skill release verifier'
Require-Path 'scripts\tests\verify_stock_detail_skill_discovery.mjs' 'stock-detail DSH discovery test'
Require-Path 'scripts\tests\verify_skill14_packaged_runtime.mjs' 'Skill14 packaged runtime and DSH discovery test'
Require-Path '.runtime\node\node.exe' 'bundled Node'
Require-Path '.runtime\python\python.exe' 'bundled Python'
Require-Path 'harness-headless.patch.yml' 'Harness headless patch'
Require-Path 'electron-app\main.mjs' 'Electron main process'
Require-Path 'electron-app\preload.cjs' 'Electron preload bridge'
Require-Path 'electron-app\runtime-ports.mjs' 'desktop port allocator'
Require-Path 'electron-app\electron-builder.yml' 'Electron builder config'
Require-Path 'electron-app\runtime-manifest.json' 'desktop runtime manifest'
Require-Path 'packaging\staging\desktop-runtime\manifest.json' 'pruned reusable desktop environment layer'
Require-Path 'packaging\staging\desktop-runtime\deepseek-harness\node_modules\yaml\dist\doc\directives.js' 'Harness YAML runtime directive module'
Require-Path 'packaging\environment-baseline-version.txt' 'environment baseline version'
Require-Path 'app-data\evidence\formulas\package\manifest.json' 'portable TQ formula seed source'
Require-Path 'packaging\dependency-manifest.json' 'desktop dependency manifest'
Require-Path 'packaging\main-installer-policy.json' 'main installer packaging policy'
Require-Path 'electron-app\resources\zhangcai-icon.png' 'desktop icon'
Require-Path 'electron-app\resources\zhangcai-icon-256.png' 'normalized desktop icon'
Require-Path 'electron-app\resources\zhangcai-icon.ico' 'Windows desktop icon'
Require-Path 'electron-app\resources\installer-icon.ico' 'Windows installer icon'
if (-not $MainInstaller) {
  Require-Path 'packaging\data-pack-icon.png' 'data-pack icon'
  Require-Path 'packaging\data-pack-README.md' 'data-pack README'
  Require-Path 'packaging\data-pack-icon.ico' 'data-pack installer icon'
  Require-Path 'scripts\convert-data-pack-icon.mjs' 'data-pack icon converter'
  Require-Path 'scripts\package-data-installer.ps1' 'data-pack installer build script'
  Require-Path 'scripts\build-canonical-daily-index.mjs' 'canonical daily index builder'
  Require-Path 'electron-app\nsis\data-pack-installer.nsi' 'data-pack installer script'
}
Require-Path 'electron-app\nsis\program-update-installer.nsi' 'program update installer script'
Require-Path 'electron-app\nsis\environment-installer.nsi' 'environment installer script'
Require-Path 'electron-app\nsis\environment-uninstaller.nsi' 'environment uninstaller script'
Require-Path 'electron-app\nsis\tdx-selection.nsh' 'TDX installer page'
Require-Path 'packaging\runtime-node-modules\vinext\dist\cli.js' 'production Vinext runtime'

if ($MainInstaller) {
  $builderConfigPath = Join-Path $projectRoot 'electron-app\electron-builder.yml'
  $mainBuildScriptPath = Join-Path $projectRoot 'scripts\package-win.ps1'
  $builderText = if (Test-Path -LiteralPath $builderConfigPath) { Get-Content -LiteralPath $builderConfigPath -Raw -Encoding UTF8 } else { '' }
  $mainBuildText = if (Test-Path -LiteralPath $mainBuildScriptPath) { Get-Content -LiteralPath $mainBuildScriptPath -Raw -Encoding UTF8 } else { '' }
  $expectedSiteBuildMapping = "packaging/staging/site-build-$($package.version)/dist"
  if ($builderText.IndexOf($expectedSiteBuildMapping, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) {
    $errors.Add("Main installer frontend mapping must match package version $($package.version): $expectedSiteBuildMapping")
  }
  $expectedReleaseDirectory = "dist-installer/releases/$($package.version)"
  if ($builderText.IndexOf($expectedReleaseDirectory, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) {
    $warnings.Add("Electron builder default output path is not pinned to current package version $($package.version); package-win must pass the immutable release output explicitly.")
  }

  foreach ($requiredMapping in @(
    'packaging/staging/desktop-runtime/app-node-modules',
    'packaging/staging/desktop-runtime/python',
    'packaging/staging/desktop-runtime/deepseek-harness',
    'electron-app/resource-library',
    'from: harness-skills',
    'to: app/harness-skills',
    'from: skill-archives',
    'to: app/skill-archives'
  )) {
    if ($builderText.IndexOf($requiredMapping, [System.StringComparison]::OrdinalIgnoreCase) -lt 0) {
      $errors.Add("Main installer builder is missing required baseline mapping: $requiredMapping")
    }
  }

  $archiveVerifier = Join-Path $projectRoot 'scripts\verify_skill14_archives.py'
  $archivePython = Join-Path $projectRoot '.runtime\python\python.exe'
  if ((Test-Path -LiteralPath $archiveVerifier -PathType Leaf) -and (Test-Path -LiteralPath $archivePython -PathType Leaf)) {
    $archiveOutput = & $archivePython -B $archiveVerifier 2>&1
    $archiveExitCode = $LASTEXITCODE
    try {
      $archiveReport = ($archiveOutput -join "`n") | ConvertFrom-Json
      if ($archiveExitCode -ne 0 -or $archiveReport.status -ne 'CLEAN_PASS' -or $archiveReport.checked_count -ne 14) {
        $details = @($archiveReport.errors) -join '; '
        if (-not $details) { $details = "status=$($archiveReport.status); checked=$($archiveReport.checked_count)" }
        $errors.Add("Skill14 archive release gate failed: $details")
      }
    }
    catch {
      $errors.Add("Skill14 archive release verifier returned invalid JSON: $($_.Exception.Message)")
    }
  }
  else {
    $errors.Add('Skill14 archive verification requires the bundled Python runtime and scripts/verify_skill14_archives.py.')
  }

  $skill14RuntimeTest = Join-Path $projectRoot 'scripts\tests\verify_skill14_packaged_runtime.mjs'
  $skill14Node = Join-Path $projectRoot '.runtime\node\node.exe'
  $skill14DshRoot = Join-Path $projectRoot 'packaging\staging\desktop-runtime\deepseek-harness'
  if ((Test-Path -LiteralPath $skill14RuntimeTest -PathType Leaf) -and (Test-Path -LiteralPath $skill14Node -PathType Leaf) -and (Test-Path -LiteralPath $skill14DshRoot -PathType Container) -and (Test-Path -LiteralPath $archivePython -PathType Leaf)) {
    $runtimeTestEnvNames = @('ZHANGCAI_RELEASE_APP_ROOT', 'ZHANGCAI_RELEASE_DSH_ROOT', 'ZHANGCAI_RELEASE_PYTHON')
    $runtimeTestOldEnv = @{}
    foreach ($name in $runtimeTestEnvNames) { $runtimeTestOldEnv[$name] = [Environment]::GetEnvironmentVariable($name) }
    try {
      $env:ZHANGCAI_RELEASE_APP_ROOT = $projectRoot
      $env:ZHANGCAI_RELEASE_DSH_ROOT = $skill14DshRoot
      $env:ZHANGCAI_RELEASE_PYTHON = $archivePython
      $runtimeTestOutput = & $skill14Node $skill14RuntimeTest 2>&1
      $runtimeTestExitCode = $LASTEXITCODE
    }
    finally {
      foreach ($name in $runtimeTestEnvNames) { [Environment]::SetEnvironmentVariable($name, $runtimeTestOldEnv[$name]) }
    }
    try {
      $runtimeTestReport = ($runtimeTestOutput -join "`n") | ConvertFrom-Json
      if ($runtimeTestExitCode -ne 0 -or $runtimeTestReport.status -ne 'CLEAN_PASS' -or $runtimeTestReport.prepared -ne 14 -or $runtimeTestReport.discovered -ne 14) {
        $errors.Add("Skill14 packaged runtime release gate failed: prepared=$($runtimeTestReport.prepared); DSH=$($runtimeTestReport.discovered); status=$($runtimeTestReport.status)")
      }
    }
    catch {
      $errors.Add("Skill14 packaged runtime verifier returned invalid JSON: $($_.Exception.Message)")
    }
  }
  else {
    $errors.Add('Skill14 packaged runtime test requires the bundled Python/Node runtimes and staged Harness provider.')
  }

  $stockSkillVerifier = Join-Path $projectRoot 'scripts\verify_stock_detail_skills.py'
  if ((Test-Path -LiteralPath $stockSkillVerifier -PathType Leaf) -and (Test-Path -LiteralPath $archivePython -PathType Leaf)) {
    $stockSkillOutput = & $archivePython -B $stockSkillVerifier 2>&1
    $stockSkillExitCode = $LASTEXITCODE
    try {
      $stockSkillReport = ($stockSkillOutput -join "`n") | ConvertFrom-Json
      if ($stockSkillExitCode -ne 0 -or $stockSkillReport.status -ne 'CLEAN_PASS' -or $stockSkillReport.expected_skills -ne 10 -or $stockSkillReport.selftests_passed -ne 10 -or $stockSkillReport.dsh_discovered -ne 10) {
        $details = @($stockSkillReport.errors) -join '; '
        if (-not $details) { $details = "status=$($stockSkillReport.status); selftests=$($stockSkillReport.selftests_passed)/10; DSH=$($stockSkillReport.dsh_discovered)/10" }
        $errors.Add("Stock-detail skill release gate failed: $details")
      }
    }
    catch {
      $errors.Add("Stock-detail skill release verifier returned invalid JSON: $($_.Exception.Message)")
    }
  }
  else {
    $errors.Add('Stock-detail skill verification requires the bundled Python runtime and scripts/verify_stock_detail_skills.py.')
  }

  foreach ($forbiddenMapping in @(
    'app-data',
    'dist-installer/data-pack',
    'data-pack-*'
  )) {
    if ($builderText.IndexOf($forbiddenMapping, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
      $errors.Add("Main installer builder must not reference independent data-pack content: $forbiddenMapping")
    }
  }

  foreach ($forbiddenBuildToken in @(
    'stage-exe-data.ps1',
    'package-data-installer.ps1',
    'package:data'
  )) {
    if ($mainBuildText.IndexOf($forbiddenBuildToken, [System.StringComparison]::OrdinalIgnoreCase) -ge 0) {
      $errors.Add("Main installer build script must not invoke a data-pack step: $forbiddenBuildToken")
    }
  }
}

$harnessCandidates = @(
  (Join-Path $projectRoot '.runtime\deepseek-harness\lib\bin.js'),
  (Join-Path $projectRoot 'runtime\deepseek-harness\lib\bin.js'),
  (Join-Path $projectRoot 'packaging\vendor\deepseek-harness\lib\bin.js')
)
$harnessReady = $harnessCandidates | Where-Object { Test-Path -LiteralPath $_ } | Select-Object -First 1
if (-not $harnessReady) {
  $message = 'No bundled DeepSeek Harness entry found (lib/bin.js).'
  if ($RequireHarnessRuntime) { $errors.Add($message) } else { $warnings.Add($message) }
}
else {
  $harnessNodeModules = Join-Path $projectRoot 'packaging\vendor\deepseek-harness\node_modules'
  if (-not (Test-Path -LiteralPath (Join-Path $harnessNodeModules '@deepseek-ai\dsh-app-boot'))) {
    $message = 'Bundled DeepSeek Harness dependencies are incomplete (dsh-app-boot missing).'
    if ($RequireHarnessRuntime) { $errors.Add($message) } else { $warnings.Add($message) }
  }
  $harnessNode = Join-Path $projectRoot '.runtime\node\node.exe'
  if (Test-Path -LiteralPath $harnessNode) {
    Push-Location (Split-Path -Parent $harnessReady)
    try {
      $harnessVersion = & $harnessNode (Split-Path -Leaf $harnessReady) '--version' 2>$null
      if ($LASTEXITCODE -ne 0 -or ($harnessVersion -join '').Trim() -ne '0.1.2-rc.1') {
        $message = "Bundled DeepSeek Harness --version failed with exit code $LASTEXITCODE."
        if ($RequireHarnessRuntime) { $errors.Add($message) } else { $warnings.Add($message) }
      }
    }
    finally {
      Pop-Location
    }
  }
}

$devDependencyNames = @($package.devDependencies.PSObject.Properties | ForEach-Object { $_.Name })
$hasElectron = $false
$hasElectronBuilder = $false
foreach ($name in $devDependencyNames) {
  if ($name -eq 'electron') { $hasElectron = $true }
  if ($name -eq 'electron-builder') { $hasElectronBuilder = $true }
}
$builderShim = Join-Path $projectRoot 'node_modules\.bin\electron-builder.cmd'
$builderCli = Join-Path $projectRoot 'node_modules\electron-builder\cli.js'
$builderNode = Join-Path $projectRoot '.runtime\node\node.exe'
$builderEntrypointReady = (Test-Path -LiteralPath $builderShim -PathType Leaf) -or ((Test-Path -LiteralPath $builderCli -PathType Leaf) -and (Test-Path -LiteralPath $builderNode -PathType Leaf))
$builderPackageFile = Join-Path $projectRoot 'node_modules\electron-builder\package.json'
if ($builderEntrypointReady -and (Test-Path -LiteralPath $builderPackageFile -PathType Leaf)) {
  try {
    $installedBuilder = Get-Content -LiteralPath $builderPackageFile -Raw -Encoding UTF8 | ConvertFrom-Json
    $pinnedBuilderVersion = [string]$package.devDependencies.'electron-builder'
    if ($installedBuilder.version -ne $pinnedBuilderVersion) {
      $builderEntrypointReady = $false
      $errors.Add("Installed electron-builder version $($installedBuilder.version) does not match pinned package version $pinnedBuilderVersion.")
    }
  } catch {
    $builderEntrypointReady = $false
    $errors.Add("Installed electron-builder package metadata is invalid: $($_.Exception.Message)")
  }
}
$electronReady = $hasElectron -and $hasElectronBuilder -and $builderEntrypointReady
if (-not $electronReady) {
  $message = 'Electron runtime or the pinned electron-builder CLI is unavailable.'
  if ($MainInstaller) { $errors.Add($message) } else { $warnings.Add($message) }
}

if (Test-Path -LiteralPath (Join-Path $projectRoot '.env.local')) {
  $warnings.Add('.env.local exists and must not enter the installer.')
}

if ($CheckRunning) {
  foreach ($port in @(3003, 4319)) {
    $listener = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue
    if (-not $listener) { $warnings.Add("Port $port is not listening; static packaging can continue but runtime preflight is incomplete.") }
  }
}

function Get-TreeBytes([string]$relativePath) {
  $target = Join-Path $projectRoot $relativePath
  if (-not (Test-Path -LiteralPath $target)) { return 0 }
  $sum = (Get-ChildItem -LiteralPath $target -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
  if ($null -eq $sum) { return 0 }
  return [int64]$sum
}

$sizes = [ordered]@{}
$sizeEntries = @('.runtime', 'node_modules', 'packaging\runtime-node-modules', 'packaging\staging\desktop-runtime', 'harness-skills', 'skill-archives', 'dist', 'packaging\vendor\deepseek-harness', 'electron-app')
if (-not $MainInstaller) { $sizeEntries += 'app-data' }
foreach ($entry in $sizeEntries) {
  $sizes[$entry] = Get-TreeBytes $entry
}

$status = 'READY'
if ($errors.Count -gt 0) { $status = 'BLOCKED' }
elseif ($warnings.Count -gt 0) { $status = 'READY_WITH_WARNINGS' }
$environmentUninstallerLabel = -join @([char]0x638C, [char]0x8D22, [char]0x684C, [char]0x9762, [char]0x7AEF, [char]0x8FD0, [char]0x884C, [char]0x73AF, [char]0x5883, [char]0x5378, [char]0x8F7D)

[pscustomobject]@{
  schema = 'ZHANGCAI_PACKAGE_PREFLIGHT_V1'
  projectRoot = $projectRoot
  packageVersion = $package.version
  nodeEngine = $package.engines.node
  frontend = @{ desktopPreferredPort = 34303; primaryRoute = '/'; chatRoute = '/chat'; legacyWebPorts = @(3003, 3004) }
  bridge = @{ desktopPreferredPort = 44319; legacyWebPort = 4319; host = '127.0.0.1' }
  portIsolation = @{ desktopNeverUses = @(3003, 3004, 4319); identityCheck = 'health.appRoot-and-dataRoot' }
  packagingPolicy = @{ mode = if ($MainInstaller) { 'main-installer-embeds-baseline-bypasses-independent-data-pack' } else { 'full-packaging-toolchain-check' }; policyFile = 'packaging/main-installer-policy.json'; dataPackInput = if ($MainInstaller) { 'not-read-not-required-not-merged' } else { 'separate-artifact-only' }; baselineRuntime = 'embedded-in-main-installer-and-reused-by-program-updates'; appDataMeasured = (-not $MainInstaller) }
  desktopShell = @{ chatIntegrated = $true; lastPagePersisted = $true; browserStoragePersisted = $true; icon = 'electron-app/resources/zhangcai-icon.ico'; installerIcon = 'electron-app/resources/installer-icon.ico'; dataPackIcon = 'packaging/data-pack-icon.png'; dataPackInstallerIcon = 'packaging/data-pack-icon.ico'; dataPackInstaller = 'electron-app/nsis/data-pack-installer.nsi'; dependenciesEmbedded = $true; mainProgramRequiresEnvironment = $false; portableTdxFormulaSeed = 'embedded-in-main-program-and-merged-on-first-launch'; environmentLayer = 'embedded in the main installer and reused by later program updates: resources/runtime + resources/deepseek-harness + resources/app/node_modules'; environmentInstaller = 'scripts/stage-desktop-runtime.ps1 (build cache only; not a prerequisite installer)'; environmentUninstaller = ($environmentUninstallerLabel + '-<version>-x64.exe (legacy/optional)'); programUpdate = 'scripts/package-program-update.ps1' }
  harnessReady = [bool]$harnessReady
  harnessEntry = if ($harnessReady) { $harnessReady } else { '' }
  electronReady = $electronReady
  electronBuilderInvocation = if (Test-Path -LiteralPath $builderShim -PathType Leaf) { 'cmd-shim' } elseif ($builderEntrypointReady) { 'bundled-node-cli' } else { 'missing' }
  sizesBytes = $sizes
  errors = @($errors)
  warnings = @($warnings)
  status = $status
} | ConvertTo-Json -Depth 8

if ($errors.Count -gt 0) { exit 1 }
