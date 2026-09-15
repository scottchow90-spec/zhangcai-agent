$ErrorActionPreference = 'Stop'

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
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
  }
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

# Verify the frontend and all referenced client chunks.
$frontHealthy = Test-Http200 'http://127.0.0.1:3003/'
$frontAssetHealthy = $false
if ($frontHealthy) {
  & $runtimeNode (Join-Path $appRoot 'scripts\verify-served-assets.mjs') 'http://127.0.0.1:3003/' 2>$null | Out-Null
  $frontAssetHealthy = $LASTEXITCODE -eq 0
}
if (-not ($frontHealthy -and $frontAssetHealthy)) {
  Stop-ListeningPids 3003
  $frontOut = Join-Path $appRoot 'prod-server-3003.out.log'
  $frontErr = Join-Path $appRoot 'prod-server-3003.err.log'
  # Do not carry a previous Vinext client-disconnect record into the next
  # startup check; the log must describe the current frontend process.
  Set-Content -LiteralPath $frontOut -Value '' -Encoding utf8
  Set-Content -LiteralPath $frontErr -Value '' -Encoding utf8
  Start-Process -FilePath 'pnpm.cmd' -ArgumentList @('start') -WorkingDirectory $appRoot -WindowStyle Hidden -RedirectStandardOutput $frontOut -RedirectStandardError $frontErr | Out-Null
  $frontReady = $false
  for ($attempt = 0; $attempt -lt 60; $attempt++) {
    Start-Sleep -Milliseconds 500
    if (Test-Http200 'http://127.0.0.1:3003/') {
      & $runtimeNode (Join-Path $appRoot 'scripts\verify-served-assets.mjs') 'http://127.0.0.1:3003/' 2>$null | Out-Null
      if ($LASTEXITCODE -eq 0) { $frontReady = $true; break }
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
