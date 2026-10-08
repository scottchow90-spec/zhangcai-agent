param(
  [Parameter(Mandatory = $true)][string]$SourceRoot,
  [Parameter(Mandatory = $true)][string]$PnpmRoot,
  [Parameter(Mandatory = $true)][string]$SevenZipRoot
)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$source = (Resolve-Path -LiteralPath $SourceRoot).Path
$version = '0.1.22'
$assets = Join-Path $project 'development-assets'
$releases = Join-Path $project "release-assets/$version"
New-Item -ItemType Directory -Path $assets,$releases -Force | Out-Null
$temp = Join-Path $project ('.bootstrap-tools-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $temp -Force | Out-Null
function Record-Asset([string]$file) {
  $item = Get-Item -LiteralPath $file
  return [ordered]@{ path = [IO.Path]::GetRelativePath($project, $item.FullName).Replace('\','/'); bytes = $item.Length; sha256 = (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash.ToLowerInvariant() }
}
try {
  Copy-Item -LiteralPath (Join-Path $source "dist-installer/releases/$version/掌财桌面端-$version-x64.exe") -Destination (Join-Path $releases "zhangcai-desktop-$version-x64.exe")
  Copy-Item -LiteralPath (Join-Path $source "dist-installer/releases/$version/掌财桌面端-程序更新-$version-x64.exe") -Destination (Join-Path $releases "zhangcai-desktop-update-$version-x64.exe")
  Copy-Item -LiteralPath $PnpmRoot -Destination (Join-Path $temp 'pnpm') -Recurse
  Copy-Item -LiteralPath $SevenZipRoot -Destination (Join-Path $temp '7zip') -Recurse
  New-Item -ItemType Directory -Path (Join-Path $temp 'python/Lib') -Force | Out-Null
  Copy-Item -LiteralPath (Join-Path $source '.runtime/python/Lib/ensurepip') -Destination (Join-Path $temp 'python/Lib/ensurepip') -Recurse
  Get-ChildItem -LiteralPath $temp -Directory -Recurse -Force | Where-Object Name -eq '__pycache__' | ForEach-Object { Remove-Item -LiteralPath $_.FullName -Recurse -Force }
  $zip = Join-Path $assets "windows-x64-dev-tools-$version.zip"
  if (Test-Path -LiteralPath $zip) { throw "Asset already exists: $zip" }
  Add-Type -AssemblyName System.IO.Compression.FileSystem
  [IO.Compression.ZipFile]::CreateFromDirectory($temp, $zip, [IO.Compression.CompressionLevel]::Optimal, $false)
  $sources = @('app/home-client.tsx','app/chat/chat-client.tsx','app/workspace-pages.tsx','app/desktop-runtime-shell.tsx','app/skill14-home.tsx','app/page.tsx','app/layout.tsx','app/chat/page.tsx','app/globals.css')
  $records = foreach ($relative in $sources) {
    $original = Join-Path $source "packaging/staging/site-work-$version/$relative"
    $current = Join-Path $project $relative
    if ((Get-FileHash -LiteralPath $original).Hash -ne (Get-FileHash -LiteralPath $current).Hash) { throw "Original build source differs: $relative" }
    Record-Asset $current
  }
  $manifest = [ordered]@{
    schema = 'ZHANGCAI_REPRODUCIBLE_DEVELOPMENT_V1'; productVersion = $version; environmentBaseline = '0.1.9'
    nodeVersion = '24.19.0'; pythonVersion = '3.12.14'; pnpmVersion = '11.19.0'; harnessVersion = '0.1.2-rc.1'
    installer = Record-Asset (Join-Path $releases "zhangcai-desktop-$version-x64.exe")
    update = Record-Asset (Join-Path $releases "zhangcai-desktop-update-$version-x64.exe")
    tools = Record-Asset $zip
    sourceProvenance = 'Original Windows 0.1.22 build workspace (site-work-0.1.22), retained before the 2026-09-25 installer build; byte-checked against the local working sources. Compiled bundles vary between the recovered update and the later full installer; no claim of byte-identical rebuild.'
    originalFrontendSources = @($records)
    externalInputs = @('User-selected TDX installation/market history', 'User-supplied DeepSeek credentials', 'npm registry packages resolved by pnpm-lock.yaml')
  }
  [IO.File]::WriteAllText((Join-Path $assets 'manifest.json'), ($manifest | ConvertTo-Json -Depth 8) + "`n", [Text.UTF8Encoding]::new($false))
  $manifest | ConvertTo-Json -Depth 8
} finally {
  $resolvedTemp = [IO.Path]::GetFullPath($temp)
  if ($resolvedTemp.StartsWith($project + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -and (Split-Path $resolvedTemp -Leaf) -like '.bootstrap-tools-*') {
    Remove-Item -LiteralPath $resolvedTemp -Recurse -Force
  }
}
