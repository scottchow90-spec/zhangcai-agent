param(
  [int]$Port = 54319
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$unpackedRoot = Join-Path $projectRoot 'dist-installer\win-unpacked'
$node = Join-Path $unpackedRoot 'resources\runtime\node\node.exe'
$entry = Join-Path $unpackedRoot 'resources\app\agent-server.mjs'
$vinext = Join-Path $unpackedRoot 'resources\app\node_modules\vinext\dist\cli.js'
$appRoot = Join-Path $unpackedRoot 'resources\app'
$dataRoot = Join-Path $env:TEMP ('zhangcai-package-smoke-' + [guid]::NewGuid().ToString('N'))

foreach ($required in @($node, $entry, $vinext, (Join-Path $unpackedRoot 'resources\deepseek-harness\lib\bin.js'))) {
  if (-not (Test-Path -LiteralPath $required)) { throw "Missing packaged smoke target: $required" }
}
New-Item -ItemType Directory -Path $dataRoot -Force | Out-Null
$stdoutLog = Join-Path $dataRoot 'stdout.log'
$stderrLog = Join-Path $dataRoot 'stderr.log'
$uiStdoutLog = Join-Path $dataRoot 'ui-stdout.log'
$uiStderrLog = Join-Path $dataRoot 'ui-stderr.log'

$names = @('ZHANGCAI_BRIDGE_PORT', 'ZHANGCAI_PACKAGED', 'ZHANGCAI_APP_ROOT', 'ZHANGCAI_DATA_DIR', 'ZHANGCAI_PYTHON', 'DSH_ENTRY', 'DSH_HOME')
$old = @{}
foreach ($name in $names) { $old[$name] = [Environment]::GetEnvironmentVariable($name) }
$env:ZHANGCAI_BRIDGE_PORT = [string]$Port
$env:ZHANGCAI_PACKAGED = '1'
$env:ZHANGCAI_APP_ROOT = $appRoot
$env:ZHANGCAI_DATA_DIR = $dataRoot
$env:ZHANGCAI_PYTHON = Join-Path $unpackedRoot 'resources\runtime\python\python.exe'
$env:DSH_ENTRY = Join-Path $unpackedRoot 'resources\deepseek-harness\lib\bin.js'
$env:DSH_HOME = Join-Path $dataRoot 'harness'

$process = Start-Process -FilePath $node -ArgumentList ('"' + $entry + '"') -WorkingDirectory $appRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput $stdoutLog -RedirectStandardError $stderrLog
$uiProcess = $null
$health = $null
try {
  for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Milliseconds 250
    try {
      $health = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/health" -TimeoutSec 2
      break
    }
    catch {
      if ($process.HasExited) {
        $stdout = if (Test-Path -LiteralPath $stdoutLog) { Get-Content -LiteralPath $stdoutLog -Raw } else { '' }
        $stderr = if (Test-Path -LiteralPath $stderrLog) { Get-Content -LiteralPath $stderrLog -Raw } else { '' }
        throw "Packaged bridge exited before health response: $($process.ExitCode)`nSTDOUT:`n$stdout`nSTDERR:`n$stderr"
      }
    }
  }
  if ($null -eq $health) { throw 'Packaged bridge health timeout' }
  $uiProcess = Start-Process -FilePath $node -ArgumentList ('"' + $vinext + '" start --hostname 127.0.0.1 --port 53003') -WorkingDirectory $appRoot -PassThru -WindowStyle Hidden -RedirectStandardOutput $uiStdoutLog -RedirectStandardError $uiStderrLog
  $uiResponses = @{}
  foreach ($route in @('/', '/chat')) {
    $response = $null
    for ($i = 0; $i -lt 30; $i++) {
      Start-Sleep -Milliseconds 250
      try {
        $response = Invoke-WebRequest -Uri ("http://127.0.0.1:53003" + $route) -UseBasicParsing -TimeoutSec 2
        break
      }
      catch {
        if ($uiProcess.HasExited) {
          $uiStderr = if (Test-Path -LiteralPath $uiStderrLog) { Get-Content -LiteralPath $uiStderrLog -Raw } else { '' }
          throw "Packaged UI exited before $route response: $($uiProcess.ExitCode)`n$uiStderr"
        }
      }
    }
    if ($null -eq $response) { throw "Packaged UI route timeout: $route" }
    $uiResponses[$route] = $response.StatusCode
  }
  [pscustomobject]@{
    status = 'PASS'
    port = $Port
    pid = $process.Id
    health = $health
    ui = $uiResponses
    dataRoot = $dataRoot
  } | ConvertTo-Json -Depth 8
}
finally {
  if ($process -and -not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
  if ($uiProcess -and -not $uiProcess.HasExited) { Stop-Process -Id $uiProcess.Id -Force -ErrorAction SilentlyContinue }
  foreach ($name in $names) { [Environment]::SetEnvironmentVariable($name, $old[$name]) }
  if (Test-Path -LiteralPath $dataRoot) { Remove-Item -LiteralPath $dataRoot -Recurse -Force -ErrorAction SilentlyContinue }
}
