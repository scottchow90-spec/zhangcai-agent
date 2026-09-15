$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
Set-Location $appRoot

# Bind the web app to the configured interface. Use netstat so this also
# works in restricted PowerShell sessions where Get-NetTCPConnection fails.
$front = netstat -ano 2>$null | Select-String ':(3001|3002)\s+.*LISTENING'
if (-not $front) {
  $out = Join-Path $appRoot 'dev-server.out.log'
  $err = Join-Path $appRoot 'dev-server.err.log'
  Start-Process -FilePath 'pnpm.cmd' -ArgumentList @('dev') `
    -WorkingDirectory $appRoot -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err
}

# A busy Harness bridge can need more than two seconds to answer /health.
# Never kill an existing listener from auto-recovery: doing so aborts every
# local and tunneled remote job. Start a bridge only when 4318 has no listener.
$bridge = netstat -ano 2>$null | Select-String ':4318\s+.*LISTENING'
$bridgeHealthy = $false
if ($bridge) {
  foreach ($attempt in 1..3) {
    try {
      $health = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:4318/health' -TimeoutSec 5
      if ($health.StatusCode -eq 200) {
        $bridgeHealthy = $true
        break
      }
    } catch {
      if ($attempt -lt 3) { Start-Sleep -Milliseconds 750 }
    }
  }
}
if (-not $bridge) {
  Start-Process -FilePath 'pnpm.cmd' -ArgumentList @('agent:dev') `
    -WorkingDirectory $appRoot -WindowStyle Hidden
} elseif (-not $bridgeHealthy) {
  Write-Warning 'Port 4318 is listening but temporarily missed health checks; preserving the existing Harness process.'
}

$addresses = @(
  ipconfig | ForEach-Object {
    if ($_ -match ':\s*((?:\d{1,3}\.){3}\d{1,3})\s*$') { $Matches[1] }
  } | Where-Object { $_ -notlike '127.*' -and $_ -notlike '169.254.*' -and $_ -notlike '255.*' } | Select-Object -Unique
)
Write-Host ('Zhangcai started: http://localhost:3001/; LAN: ' + (($addresses | ForEach-Object { "http://${_}:3001/" }) -join ', '))
