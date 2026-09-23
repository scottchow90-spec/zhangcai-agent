param(
  [Parameter(Mandatory = $true)]
  [string]$ElectronBuilder,
  [Parameter(Mandatory = $true)]
  [string]$ConfigPath,
  [Parameter(Mandatory = $true)]
  [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'

$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$nodeModulesRoot = Join-Path $projectRoot 'node_modules'

function Find-NsisTemplateRoot {
  $candidates = New-Object 'System.Collections.Generic.List[string]'
  $candidates.Add((Join-Path $nodeModulesRoot 'app-builder-lib\templates\nsis'))

  $pnpmRoot = Join-Path $nodeModulesRoot '.pnpm'
  if (Test-Path -LiteralPath $pnpmRoot) {
    Get-ChildItem -LiteralPath $pnpmRoot -Directory -Filter 'app-builder-lib@*' -ErrorAction SilentlyContinue |
      ForEach-Object {
        $candidates.Add((Join-Path $_.FullName 'node_modules\app-builder-lib\templates\nsis'))
      }
  }

  foreach ($candidate in $candidates) {
    if ((Test-Path -LiteralPath (Join-Path $candidate 'common.nsh')) -and
        (Test-Path -LiteralPath (Join-Path $candidate 'installSection.nsh')) -and
        (Test-Path -LiteralPath (Join-Path $candidate 'include\extractAppPackage.nsh'))) {
      return $candidate
    }
  }

  throw 'Cannot locate electron-builder NSIS templates; visible installer details were not enabled.'
}

function Write-Utf8WithBom([string]$path, [string]$content) {
  # NSIS templates are parsed on the target machine's system code page when
  # the UTF-8 signature is absent. Keep the BOM so GBK Windows does not turn
  # the injected Chinese DetailPrint text into mojibake.
  $utf8WithBom = New-Object System.Text.UTF8Encoding($true)
  [System.IO.File]::WriteAllText($path, $content, $utf8WithBom)
}

$templateRoot = Find-NsisTemplateRoot
$templatePaths = @(
  (Join-Path $templateRoot 'common.nsh'),
  (Join-Path $templateRoot 'installSection.nsh'),
  (Join-Path $templateRoot 'include\extractAppPackage.nsh')
)
$originalBytes = @{}

try {
  foreach ($templatePath in $templatePaths) {
    $originalBytes[$templatePath] = [System.IO.File]::ReadAllBytes($templatePath)
  }

  $commonPath = $templatePaths[0]
  $common = [System.IO.File]::ReadAllText($commonPath)
  if (-not $common.Contains('ShowInstDetails nevershow')) {
    throw "Unexpected electron-builder template: $commonPath"
  }
  $common = $common.Replace('ShowInstDetails nevershow', 'ShowInstDetails show')
  Write-Utf8WithBom $commonPath $common

  $installSectionPath = $templatePaths[1]
  $installSection = [System.IO.File]::ReadAllText($installSectionPath)
  if (-not $installSection.Contains('SetDetailsPrint none')) {
    throw "Unexpected electron-builder template: $installSectionPath"
  }
  $installSection = $installSection.Replace('SetDetailsPrint none', 'SetDetailsPrint both')
  Write-Utf8WithBom $installSectionPath $installSection

  $extractPath = $templatePaths[2]
  $extract = [System.IO.File]::ReadAllText($extractPath)
  $extractMarker = '  Nsis7z::Extract "${FILE}"'
  if (-not $extract.Contains($extractMarker)) {
    throw "Unexpected electron-builder template: $extractPath"
  }
  $extract = $extract.Replace(
    $extractMarker,
    '  DetailPrint "File group: Zhangcai Desktop application, embedded Harness and TQ formula seed"' + [Environment]::NewLine + $extractMarker
  )
  Write-Utf8WithBom $extractPath $extract

  Write-Output "NSIS installer detail mode enabled: $templateRoot"
  & $ElectronBuilder '--config' $ConfigPath "--config.directories.output=$OutputDirectory"
  $buildExitCode = $LASTEXITCODE
}
finally {
  foreach ($templatePath in $originalBytes.Keys) {
    [System.IO.File]::WriteAllBytes($templatePath, $originalBytes[$templatePath])
  }
  Write-Output 'NSIS templates restored.'
}

if ($null -eq $buildExitCode) {
  $buildExitCode = 1
}
exit $buildExitCode
