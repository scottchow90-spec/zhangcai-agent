param(
  [string]$WorkspaceRoot = ''
)

$ErrorActionPreference = 'Stop'
if (-not $WorkspaceRoot) { $WorkspaceRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path }
$workspace = [System.IO.Path]::GetFullPath($WorkspaceRoot).TrimEnd('\').ToLowerInvariant()

# Never stop the web-test stack. Protect the listeners and their descendants,
# because the bridge may have spawned a Python worker that does not own a port.
$protected = New-Object 'System.Collections.Generic.HashSet[int]'
foreach ($port in @(3003, 3004, 4319)) {
  Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue |
    ForEach-Object { [void]$protected.Add([int]$_.OwningProcess) }
}
$processes = @(Get-CimInstance Win32_Process)
$ancestors = New-Object 'System.Collections.Generic.HashSet[int]'
$ancestorId = $PID
while ($ancestorId -gt 0 -and $ancestors.Add([int]$ancestorId)) {
  $ancestor = $processes | Where-Object { $_.ProcessId -eq $ancestorId } | Select-Object -First 1
  if (-not $ancestor) { break }
  $ancestorId = [int]$ancestor.ParentProcessId
}
$changed = $true
while ($changed) {
  $changed = $false
  foreach ($process in $processes) {
    if ($protected.Contains([int]$process.ParentProcessId) -and $protected.Add([int]$process.ProcessId)) { $changed = $true }
  }
}

$targets = New-Object 'System.Collections.Generic.List[object]'
foreach ($process in $processes) {
  $processId = [int]$process.ProcessId
  if ($protected.Contains($processId) -or $ancestors.Contains($processId)) { continue }
  $name = [string]$process.Name
  $command = [string]$process.CommandLine
  $commandLower = $command.ToLowerInvariant()
  $inWorkspace = $commandLower.Contains($workspace)
  if (-not $inWorkspace) { continue }

  $isProjectPython = $name -match '^(python|pythonw)(\.exe)?$' -and $commandLower -match 'scripts[\\/]|skill14|tdx_|harness-skills|selection_score'
  $isHarness = $commandLower -match 'deepseek-harness|@deepseek-ai[\\/]dsh|(^|[\\/])dsh([\\.]|[\\/])|hermes'
  $isPackagingTool = $name -match '^(7za|makensis|electron-builder|electron|node)(\.exe)?$' -and
    $commandLower -match 'electron-builder|makensis|vinext[\s]+build|7za\.exe.*dist-installer|package-win|package-data-installer'
  $isPackagingLauncher = $name -match '^(cmd|conhost)(\.exe)?$' -and
    $commandLower -match 'electron-builder|makensis|vinext[\s]+build|package-win|package-data-installer'
  $isPackaging = $isPackagingTool -or $isPackagingLauncher
  if (-not ($isProjectPython -or $isHarness -or $isPackaging)) { continue }

  $targets.Add([pscustomobject]@{ ProcessId = $processId; Name = $name; CommandLine = $command })
}

foreach ($target in $targets) {
  try {
    Stop-Process -Id $target.ProcessId -Force -ErrorAction Stop
    Write-Output ("Stopped packaging-locking process {0} ({1})" -f $target.ProcessId, $target.Name)
  } catch {
    Write-Warning ("Could not stop process {0}: {1}" -f $target.ProcessId, $_.Exception.Message)
  }
}

[pscustomobject]@{
  status = 'PASS'
  workspace = $WorkspaceRoot
  protectedWebPorts = @(3003, 3004, 4319)
  protectedProcessCount = $protected.Count
  stoppedProcessCount = $targets.Count
  stopped = @($targets | ForEach-Object { @{ pid = $_.ProcessId; name = $_.Name } })
} | ConvertTo-Json -Depth 6
