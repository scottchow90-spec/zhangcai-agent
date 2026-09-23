$ErrorActionPreference = 'Stop'
# A failed asset probe intentionally returns a non-zero native exit code. Do
# not let PowerShell turn the probe's stderr into a terminating exception
# before the recovery branch can restart the stale frontend process.
$PSNativeCommandUseErrorActionPreference = $false

# Use the application working directory for both pnpm and packaged launches.
$appRoot = (Get-Location).Path
if (-not $appRoot) { throw '3003 launcher could not resolve the application directory.' }
if (-not (Test-Path -LiteralPath (Join-Path $appRoot 'package.json'))) {
  $candidateRoot = Join-Path $appRoot 'zhangcai-web-3003'
  if (Test-Path -LiteralPath (Join-Path $candidateRoot 'package.json')) { $appRoot = $candidateRoot }
}
Set-Location -LiteralPath $appRoot

$env:ZHANGCAI_APP_ROOT = $appRoot
$env:ZHANGCAI_BRIDGE_PORT = '4319'
$env:ZHANGCAI_DATA_DIR = Join-Path $appRoot 'app-data'

function Get-ListeningPids([int]$port) {
  $result = @()
  try {
    $connections = Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction Stop
    foreach ($connection in $connections) {
      if ($connection.OwningProcess -and $connection.OwningProcess -gt 0) { $result += [int]$connection.OwningProcess }
    }
  } catch {
    $lines = netstat -ano 2>$null | Select-String (":$port\s+.*LISTENING")
    foreach ($line in $lines) {
      if ($line.ToString() -match '\s(?<pid>\d+)\s*$') { $result += [int]$Matches.pid }
    }
  }
  return @($result | Select-Object -Unique)
}

function Stop-ListeningPids([int]$port) {
  foreach ($processId in (Get-ListeningPids $port)) {
    $processInfo = Get-CimInstance Win32_Process -Filter "ProcessId=$processId" -ErrorAction SilentlyContinue
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue

    # pnpm.cmd starts Vinext through a cmd.exe parent. Killing only the
    # listener leaves that parent holding redirected log files and can also
    # leave a stale production process tree behind. Only terminate the parent
    # when its command line is the verified frontend for this exact port.
    if ($processInfo -and $processInfo.ParentProcessId) {
      $parent = Get-CimInstance Win32_Process -Filter "ProcessId=$($processInfo.ParentProcessId)" -ErrorAction SilentlyContinue
      if ($parent -and $parent.Name -eq 'cmd.exe' -and $parent.CommandLine -match "vinext start.*port $port") {
        Stop-Process -Id ([int]$parent.ProcessId) -Force -ErrorAction SilentlyContinue
      }
    }
  }
}

function Stop-FrontendProcesses([int]$port) {
  Stop-ListeningPids $port
  # A failed launch can leave pnpm/cmd alive after the listener has already
  # exited.  Match only the exact Vinext production command and port; never
  # terminate the separate 3002/4318 runtime.
  $candidates = Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -match "vinext\s+start.*(?:--port\s+|port\s+)$port\b" }
  foreach ($candidate in $candidates) {
    & taskkill.exe /PID ([int]$candidate.ProcessId) /T /F *> $null
  }
  Start-Sleep -Milliseconds 250
  Stop-ListeningPids $port
}

function Test-Http200([string]$url) {
  try {
    $status = (& curl.exe --max-time 3 -s -o NUL -w '%{http_code}' $url 2>$null).Trim()
    return $status -eq '200'
  } catch {
    return $false
  }
}

# Prefer the Node runtime shipped inside the application.
$runtimeNode = '.runtime\node\node.exe'
if (-not (Test-Path -LiteralPath $runtimeNode)) { $runtimeNode = 'runtime\node\node.exe' }
if (-not (Test-Path -LiteralPath $runtimeNode)) {
  $pathNode = Get-Command 'node.exe' -ErrorAction SilentlyContinue
  if ($pathNode -and $pathNode.Source -notmatch '\.cache[\\/]codex-runtimes[\\/]') { $runtimeNode = $pathNode.Source }
}
if (-not (Test-Path -LiteralPath $runtimeNode)) {
  throw '3003 application-local Node.js runtime not found under .runtime\node\node.exe.'
}
$runtimeNode = (Resolve-Path -LiteralPath $runtimeNode).Path
$env:Path = "$(Split-Path -Parent $runtimeNode);$env:Path"

function Test-ServedAssets([string]$url) {
  try {
    & $runtimeNode (Join-Path $appRoot 'scripts\verify-served-assets.mjs') $url 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
  } catch {
    return $false
  }
}

# Verify the frontend and all referenced client chunks.
$frontHealthy = Test-Http200 'http://127.0.0.1:3003/'
$frontAssetHealthy = $false
if ($frontHealthy) {
  $frontAssetHealthy = Test-ServedAssets 'http://127.0.0.1:3003/'
}
if (-not ($frontHealthy -and $frontAssetHealthy)) {
  Stop-FrontendProcesses 3003
  # Use a fresh log pair for every launch.  A previous pnpm/cmd process may
  # still hold a redirected handle for a short time even after its listener
  # exits; reusing the fixed file made recovery fail before the new server
  # could start.
  $logRoot = Join-Path $appRoot 'app-data\runtime\logs'
  New-Item -ItemType Directory -Force -Path $logRoot | Out-Null
  $launchStamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
  $frontOut = Join-Path $logRoot "prod-server-3003-$launchStamp.out.log"
  $frontErr = Join-Path $logRoot "prod-server-3003-$launchStamp.err.log"
  Start-Process -FilePath 'pnpm.cmd' -ArgumentList @('start') -WorkingDirectory $appRoot -WindowStyle Hidden -RedirectStandardOutput $frontOut -RedirectStandardError $frontErr | Out-Null
  $frontReady = $false
  for ($attempt = 0; $attempt -lt 60; $attempt++) {
    Start-Sleep -Milliseconds 500
    if (Test-Http200 'http://127.0.0.1:3003/') {
      if (Test-ServedAssets 'http://127.0.0.1:3003/') { $frontReady = $true; break }
    }
  }
  if (-not $frontReady) { throw "3003 frontend failed the client asset check. See $frontErr." }
}

# Verify the bridge is the current 3003 bridge, not an old process on the port.
$bridgeHealthy = $false
try {
  $health = (& curl.exe --max-time 3 -s 'http://127.0.0.1:4319/health' 2>$null).Trim()
  $bridgeHealthy = $health -match 'runtime/tdx/open'
} catch { $bridgeHealthy = $false }
if (-not $bridgeHealthy) {
  Stop-ListeningPids 4319
  $bridgeOut = Join-Path $appRoot 'bridge-server.out.log'
  $bridgeErr = Join-Path $appRoot 'bridge-server.err.log'
  Start-Process -FilePath $runtimeNode -ArgumentList @('agent-server.mjs') -WorkingDirectory $appRoot -WindowStyle Hidden -RedirectStandardOutput $bridgeOut -RedirectStandardError $bridgeErr | Out-Null
  $bridgeReady = $false
  for ($attempt = 0; $attempt -lt 30; $attempt++) {
    Start-Sleep -Milliseconds 500
    try {
      $status = (& curl.exe --max-time 2 -s -o NUL -w '%{http_code}' 'http://127.0.0.1:4319/health' 2>$null).Trim()
      $payload = (& curl.exe --max-time 2 -s 'http://127.0.0.1:4319/health' 2>$null).Trim()
      if ($status -eq '200' -and $payload -match 'runtime/tdx/open') { $bridgeReady = $true; break }
    } catch { }
  }
  if (-not $bridgeReady) {
    $bridgeLog = 'no bridge stderr log'
    if (Test-Path -LiteralPath $bridgeErr) { $bridgeLog = (Get-Content -LiteralPath $bridgeErr -Tail 12 -ErrorAction SilentlyContinue) -join ' ' }
    throw "3003 local bridge failed the capability health check. See $bridgeErr. $bridgeLog"
  }
}

Write-Host 'Zhangcai 14-skill runtime started: http://127.0.0.1:3003/'
