param(
  [int]$Port = 4319
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$unpackedRoot = Join-Path $projectRoot 'dist-installer\win-unpacked'
$node = Join-Path $unpackedRoot 'resources\runtime\node\node.exe'
$entry = Join-Path $unpackedRoot 'resources\app\agent-server.mjs'
$appRoot = Join-Path $unpackedRoot 'resources\app'
$dataRoot = Join-Path $env:TEMP ('zhangcai-port-conflict-' + [guid]::NewGuid().ToString('N'))
$stdoutLog = Join-Path $dataRoot 'stdout.log'
$stderrLog = Join-Path $dataRoot 'stderr.log'
$names = @('ZHANGCAI_BRIDGE_PORT', 'ZHANGCAI_PACKAGED', 'ZHANGCAI_APP_ROOT', 'ZHANGCAI_DATA_DIR', 'ZHANGCAI_PYTHON', 'DSH_ENTRY', 'DSH_HOME')
$old = @{}
$process = $null

New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
foreach ($name in $names) { $old[$name] = [Environment]::GetEnvironmentVariable($name) }
$env:ZHANGCAI_BRIDGE_PORT = [string]$Port
$env:ZHANGCAI_PACKAGED = '1'
$env:ZHANGCAI_APP_ROOT = $appRoot
$env:ZHANGCAI_DATA_DIR = $dataRoot
$env:ZHANGCAI_PYTHON = Join-Path $unpackedRoot 'resources\runtime\python\python.exe'
$env:DSH_ENTRY = Join-Path $unpackedRoot 'resources\deepseek-harness\lib\bin.js'
$env:DSH_HOME = Join-Path $dataRoot 'harness'

try {
  $process = Start-Process -FilePath $node -ArgumentList ('"' + $entry + '"') -WorkingDirectory $appRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
  Start-Sleep -Milliseconds 1500
  $existing = $null
  try { $existing = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 3 } catch { }
  $stderr = if (Test-Path -LiteralPath $stderrLog) { Get-Content -LiteralPath $stderrLog -Raw } else { '' }
  $packagedExited = if ($process) { $process.HasExited } else { $true }
  $packagedExitCode = $null
  if ($process -and $process.HasExited) { $packagedExitCode = $process.ExitCode }
  [pscustomobject]@{
    port = $Port
    packagedProcessId = if ($process) { $process.Id } else { $null }
    packagedProcessExited = $packagedExited
    packagedExitCode = $packagedExitCode
    existingHealthAppRoot = $existing.appRoot
    existingHealthDataRoot = $existing.dataRoot
    existingHealthService = $existing.service
    stderr = $stderr.Trim()
  } | ConvertTo-Json -Depth 8
}
finally {
  if ($process -and -not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
  foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name, $old[$name]) }
  if (Test-Path -LiteralPath $dataRoot) { Remove-Item -LiteralPath $dataRoot -Recurse -Force -ErrorAction SilentlyContinue }
}
