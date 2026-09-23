param(
  [switch]$SeedChatPage,
  [switch]$UseExeDataSeed,
  [switch]$VerifyReportArchive,
  [string]$UnpackedRoot = ''
)

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
if (-not $UnpackedRoot) { $UnpackedRoot = Join-Path $projectRoot 'dist-installer\win-unpacked' }
$unpackedRoot = (Resolve-Path -LiteralPath $UnpackedRoot).Path
$exe = (Get-ChildItem -LiteralPath $unpackedRoot -Filter '*.exe' -File | Select-Object -First 1).FullName
$resourceLibraryPath = Join-Path $unpackedRoot 'resources\resource-library'
$tempRoot = Join-Path $env:TEMP ('zhangcai-exe-smoke-' + [guid]::NewGuid().ToString('N'))
$runRoot = if ($UseExeDataSeed) { $resourceLibraryPath } else { $tempRoot }
$runtimeFile = Join-Path $runRoot 'desktop\runtime.json'
if (-not $exe -or -not (Test-Path -LiteralPath $exe)) { throw "Packaged EXE not found under: $unpackedRoot" }
if ($UseExeDataSeed) {
  if (-not (Test-Path -LiteralPath $resourceLibraryPath)) { throw "EXE resource library seed not found: $resourceLibraryPath. Run pnpm prepare:desktop-exe-data first." }
  foreach ($relative in @('status\tdx-daily-history.json', 'market\daily\index\tdx-symbol-index.json', 'evidence\formulas\package\manifest.json')) {
    if (-not (Test-Path -LiteralPath (Join-Path $runRoot $relative))) { throw "EXE data seed is incomplete; missing $relative" }
  }
} else {
  New-Item -ItemType Directory -Path $tempRoot -Force | Out-Null
}

$lastPageSeedFile = Join-Path $runRoot 'desktop\last-page.json'
if ($SeedChatPage) {
  New-Item -ItemType Directory -Path (Split-Path -Parent $lastPageSeedFile) -Force | Out-Null
  [System.IO.File]::WriteAllText($lastPageSeedFile, '{"schema":"ZHANGCAI_DESKTOP_LAST_PAGE_V1","path":"/chat"}', [System.Text.UTF8Encoding]::new($false))
}
$names = @('ZHANGCAI_DATA_DIR', 'ZHANGCAI_RESOURCE_LIBRARY', 'ZHANGCAI_TDX_ROOT', 'ZHANGCAI_BRIDGE_PORT', 'ZHANGCAI_PACKAGED', 'ZHANGCAI_APP_ROOT', 'DEEPSEEK_API_KEY')
$old = @{}
foreach ($name in $names) { $old[$name] = [Environment]::GetEnvironmentVariable($name) }
$env:ZHANGCAI_DATA_DIR = $runRoot
$env:ZHANGCAI_RESOURCE_LIBRARY = $runRoot
$env:ZHANGCAI_TDX_ROOT = ''
$env:ZHANGCAI_BRIDGE_PORT = ''
$env:ZHANGCAI_PACKAGED = ''
$env:ZHANGCAI_APP_ROOT = ''
$env:DEEPSEEK_API_KEY = $old['DEEPSEEK_API_KEY']
if (-not $env:DEEPSEEK_API_KEY) {
  $line = Get-Content -LiteralPath (Join-Path $projectRoot '.env.local') -ErrorAction SilentlyContinue | Where-Object { $_ -match '^\s*DEEPSEEK_API_KEY\s*=' } | Select-Object -First 1
  if ($line) {
    $value = $line.Substring($line.IndexOf('=') + 1).Trim().Trim([char]39, [char]34)
    if ($value) { $env:DEEPSEEK_API_KEY = $value }
  }
}
$process = $null
$descendants = @()

try {
  $process = Start-Process -FilePath $exe -WorkingDirectory (Split-Path -Parent $exe) -WindowStyle Hidden -PassThru
  $runtime = $null
  for ($i = 0; $i -lt 80; $i++) {
    Start-Sleep -Milliseconds 500
    if (Test-Path -LiteralPath $runtimeFile) {
      try {
        $candidate = Get-Content -LiteralPath $runtimeFile -Raw -Encoding UTF8 | ConvertFrom-Json
        if ($candidate.pid -eq $process.Id -and $candidate.desktopControlsReady -eq $true) { $runtime = $candidate; break }
      } catch {
        # Wait for the synchronous JSON write to finish on slower disks.
      }
    }
    if ($process.HasExited) { throw "EXE exited before runtime state: $($process.ExitCode)" }
  }
  if ($null -eq $runtime) { throw 'EXE runtime state timeout' }

  $bridgeUrl = "http://127.0.0.1:{0}/health" -f $runtime.bridgePort
  $bridge = Invoke-RestMethod -Uri $bridgeUrl -TimeoutSec 8
  $corsResponse = Invoke-WebRequest -Uri $bridgeUrl -Headers @{ Origin = ("http://127.0.0.1:{0}" -f $runtime.uiPort) } -UseBasicParsing -TimeoutSec 8
  $corsOrigin = $corsResponse.Headers['Access-Control-Allow-Origin']
  $ui = (Invoke-WebRequest -Uri ("http://127.0.0.1:{0}/" -f $runtime.uiPort) -UseBasicParsing -TimeoutSec 8).StatusCode
  $chat = (Invoke-WebRequest -Uri ("http://127.0.0.1:{0}/chat" -f $runtime.uiPort) -UseBasicParsing -TimeoutSec 8).StatusCode
  $environment = Invoke-RestMethod -Uri ("http://127.0.0.1:{0}/runtime/environment" -f $runtime.bridgePort) -TimeoutSec 30
  $credentials = Invoke-RestMethod -Uri ("http://127.0.0.1:{0}/runtime/credentials" -f $runtime.bridgePort) -TimeoutSec 8
  $scheduleFile = Join-Path $runRoot 'harness\schedules\after-close-daily-refresh.json'
  $schedule = $null
  for ($i = 0; $i -lt 100; $i++) {
    if (Test-Path -LiteralPath $scheduleFile) {
      try { $schedule = Get-Content -LiteralPath $scheduleFile -Raw -Encoding UTF8 | ConvertFrom-Json; break } catch { }
    }
    Start-Sleep -Milliseconds 100
  }
  if ($null -eq $schedule -or [string]$schedule.schedule -notmatch '16:30') {
    $scheduleExists = Test-Path -LiteralPath $scheduleFile
    $scheduleLength = if ($scheduleExists) { (Get-Item -LiteralPath $scheduleFile).Length } else { 0 }
    $scheduleValue = if ($null -ne $schedule) { [string]$schedule.schedule } else { '<parse-failed>' }
    throw "Desktop after-close schedule is missing or not configured for 16:30: $scheduleFile (exists=$scheduleExists length=$scheduleLength value=$scheduleValue)"
  }
  if ($schedule.dataPolicy -notin @('local_first_on_demand', 'strict_local_only')) { throw "Desktop schedule data policy mismatch: $($schedule.dataPolicy)" }
  if ($environment.minuteData.packaged -ne $false) { throw 'Desktop runtime incorrectly reports raw minute data as packaged.' }
  if ($environment.minuteData.mode -ne 'external_on_demand') { throw "Desktop minute-data mode mismatch: $($environment.minuteData.mode)" }
  $packagedMinuteFiles = @(Get-ChildItem -LiteralPath (Join-Path $unpackedRoot 'resources') -Recurse -File -Filter '*.lc5' -ErrorAction SilentlyContinue)
  if ($packagedMinuteFiles.Count -gt 0) { throw ('Packaged EXE contains raw 5-minute files: ' + ($packagedMinuteFiles.FullName -join ', ')) }
  $reportArchive = $null
  if ($VerifyReportArchive) {
    $stamp = [DateTime]::UtcNow.ToString('o')
    $reportA = [ordered]@{
      id = 'smoke-report-a-' + [guid]::NewGuid().ToString('N')
      createdAt = $stamp
      updatedAt = $stamp
      date = '20990101'
      title = 'EXE archive smoke A'
      reportType = 'archive-smoke'
      generatedBy = 'EXE smoke test'
      summary = 'new report is appended to archive'
      dataScope = 'temporary regression data'
      content = [ordered]@{ kind = 'archive-smoke'; sequence = 'A' }
      raw = 'archive smoke A'
    }
    $reportB = [ordered]@{
      id = 'smoke-report-b-' + [guid]::NewGuid().ToString('N')
      createdAt = $stamp
      updatedAt = ([DateTime]::UtcNow.AddMilliseconds(1)).ToString('o')
      date = '20990101'
      title = 'EXE archive smoke B'
      reportType = 'archive-smoke'
      generatedBy = 'EXE smoke test'
    summary = 'same-slot latest report replaces the older report'
      dataScope = 'temporary regression data'
      content = [ordered]@{ kind = 'archive-smoke'; sequence = 'B' }
      raw = 'archive smoke B'
    }
    foreach ($record in @($reportA, $reportB)) {
      $saved = Invoke-RestMethod -Method Post -Uri ("http://127.0.0.1:{0}/reports/archive" -f $runtime.bridgePort) -ContentType 'application/json' -Body ($record | ConvertTo-Json -Depth 10) -TimeoutSec 8
      if ($saved.status -ne 'ok') { throw "Report archive save failed: $($saved | ConvertTo-Json -Compress)" }
    }
    $archive = Invoke-RestMethod -Uri ("http://127.0.0.1:{0}/reports/archive" -f $runtime.bridgePort) -TimeoutSec 8
    $ids = @($archive.reports | ForEach-Object { $_.id })
    if ($ids -notcontains $reportB.id -or $ids -contains $reportA.id) {
      throw 'Report archive regression failed: the newest same-slot report was not retained while the older report was removed.'
    }
    $reportArchive = [ordered]@{ status = 'PASS'; count = @($archive.reports).Count; containsLatestReport = $true; olderSameSlotCollapsed = $true }
  }
  $loadedPage = if (Test-Path -LiteralPath $lastPageSeedFile) { (Get-Content -LiteralPath $lastPageSeedFile -Raw -Encoding UTF8 | ConvertFrom-Json).path } else { '/' }
  if ($corsOrigin -ne ("http://127.0.0.1:{0}" -f $runtime.uiPort)) { throw "Desktop CORS origin mismatch: $corsOrigin" }
  if ($runtime.bridgePort -in @(3003, 3004, 4319)) { throw "Desktop bridge incorrectly used a legacy web port: $($runtime.bridgePort)" }
  if ($bridge.resourceLibrary -ne $runRoot) { throw "Resource library identity mismatch: $($bridge.resourceLibrary)" }
  if ($bridge.dataRoot -ne $runRoot) { throw "Data root identity mismatch: $($bridge.dataRoot)" }
  if ($bridge.codePolicy -ne 'embedded-in-exe-resources') { throw "Packaged code policy mismatch: $($bridge.codePolicy)" }
  $fullData = $null
  if ($UseExeDataSeed) {
    $dataFiles = @(Get-ChildItem -LiteralPath $runRoot -Recurse -File -Force)
    $dataBytes = [int64](($dataFiles | Measure-Object -Property Length -Sum).Sum)
    $fullData = [ordered]@{ files = $dataFiles.Count; bytes = $dataBytes; GB = [math]::Round($dataBytes / 1GB, 3) }
  }
  $legacyPorts = @(3003, 3004, 4319)
  $legacyListening = @($legacyPorts | Where-Object { Get-NetTCPConnection -LocalPort $_ -State Listen -ErrorAction SilentlyContinue })

  [pscustomobject]@{
    status = 'PASS'
    exe = $exe
    pid = $process.Id
    uiPort = $runtime.uiPort
    bridgePort = $runtime.bridgePort
    loadedPage = $loadedPage
    desktopControlsReady = $runtime.desktopControlsReady
    corsOrigin = $corsOrigin
    ui = $ui
    chat = $chat
    healthStatus = $bridge.status
    healthAppRoot = $bridge.appRoot
    healthDataRoot = $bridge.dataRoot
    resourceLibrary = $bridge.resourceLibrary
    codePolicy = $bridge.codePolicy
    harnessStatus = $environment.harness.status
    credentialsConfigured = $credentials.configured
    minuteData = $environment.minuteData
    legacyWebPortsStillListening = $legacyListening
    afterCloseSchedule = [ordered]@{ schedule = $schedule.schedule; timezone = $schedule.timezone; dataPolicy = $schedule.dataPolicy; fallback = $schedule.fallback }
    fullData = $fullData
    dataSeedMode = $UseExeDataSeed.IsPresent
    reportArchive = $reportArchive
    lastPageFile = Test-Path -LiteralPath $lastPageSeedFile
  } | ConvertTo-Json -Depth 8
}
finally {
  if ($process) {
    $descendants = @(Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.ParentProcessId -eq $process.Id } | Select-Object -ExpandProperty ProcessId)
    try { $process.CloseMainWindow() | Out-Null } catch { }
    try { $process.WaitForExit(12000) | Out-Null } catch { }
    if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
    foreach ($childId in $descendants) {
      if (Get-Process -Id $childId -ErrorAction SilentlyContinue) { Stop-Process -Id $childId -Force -ErrorAction SilentlyContinue }
    }
  }
  foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name, $old[$name]) }
  if (-not $UseExeDataSeed -and (Test-Path -LiteralPath $tempRoot)) {
    $tempBase = [System.IO.Path]::GetFullPath($env:TEMP).TrimEnd('\')
    $resolvedTempRoot = [System.IO.Path]::GetFullPath($tempRoot)
    if (-not $resolvedTempRoot.StartsWith($tempBase + '\', [System.StringComparison]::OrdinalIgnoreCase) -or
        (Split-Path -Leaf $resolvedTempRoot) -notmatch '^zhangcai-exe-smoke-[0-9a-f]{32}$') {
      throw "Refusing to remove a smoke directory outside the expected temp location: $resolvedTempRoot"
    }
    Remove-Item -LiteralPath $resolvedTempRoot -Recurse -Force -ErrorAction SilentlyContinue
  }
}
