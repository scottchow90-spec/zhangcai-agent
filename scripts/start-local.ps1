$ErrorActionPreference = 'Stop'
$appRoot = Split-Path -Parent $PSScriptRoot
Set-Location $appRoot

# 绑定所有 IPv4 网卡，使同一局域网设备可以访问。用 netstat 检查端口，
# 避免权限受限时 Get-NetTCPConnection 返回空值而重复启动服务。
$front = netstat -ano 2>$null | Select-String ':3001\s+.*LISTENING'
if (-not $front) {
  $out = Join-Path $appRoot 'dev-server.out.log'
  $err = Join-Path $appRoot 'dev-server.err.log'
  Start-Process -FilePath 'pnpm.cmd' -ArgumentList @('dev') `
    -WorkingDirectory $appRoot -WindowStyle Hidden -RedirectStandardOutput $out -RedirectStandardError $err
}

# 端口仍在监听不代表桥接进程可用；网页触发恢复时先探测健康接口，
# 对“占端口但不响应”的残留进程做定向回收，避免自动恢复被假监听阻塞。
$bridgeHealthy = $false
try {
  $health = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:4318/health' -TimeoutSec 2
  $bridgeHealthy = $health.StatusCode -eq 200
} catch { $bridgeHealthy = $false }
if (-not $bridgeHealthy) {
  $bridge = netstat -ano 2>$null | Select-String ':4318\s+.*LISTENING'
  foreach ($line in $bridge) {
    if ($line.ToString() -match '\s(?<pid>\d+)\s*$') {
      Stop-Process -Id ([int]$Matches.pid) -Force -ErrorAction SilentlyContinue
    }
  }
  Start-Process -FilePath 'pnpm.cmd' -ArgumentList @('agent:dev') `
    -WorkingDirectory $appRoot -WindowStyle Hidden
}

$addresses = @(
  ipconfig | ForEach-Object {
    if ($_ -match ':\s*((?:\d{1,3}\.){3}\d{1,3})\s*$') { $Matches[1] }
  } | Where-Object { $_ -notlike '127.*' -and $_ -notlike '169.254.*' -and $_ -notlike '255.*' } | Select-Object -Unique
)
Write-Host ('Zhangcai started: http://localhost:3001/; LAN: ' + (($addresses | ForEach-Object { "http://${_}:3001/" }) -join ', '))
