param(
  [Parameter(Mandatory=$true)]
  [string]$DocxPath,
  [string]$SkillRoot = (Join-Path (Split-Path -Parent (Split-Path -Parent $PSScriptRoot)) "a-share-hotspot-sentiment-analysis\components\a-share-sentiment-workflow"),
  [string]$PdfPath = ""
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $DocxPath)) {
  throw "DOCX not found: $DocxPath"
}
if (-not (Test-Path -LiteralPath $SkillRoot)) {
  throw "Workflow skill root not found: $SkillRoot"
}

$backupOrCache = @(Get-ChildItem -LiteralPath $SkillRoot -Recurse -Force -File |
  Where-Object { $_.Name -match '\.bak|bak_' -or $_.Extension -eq '.pyc' })
if ($backupOrCache.Count -gt 0) {
  $names = ($backupOrCache | Select-Object -First 10 -ExpandProperty FullName) -join "; "
  throw "Active workflow tree contains backup/cache pollution: $names"
}

$oldDontWriteBytecode = $env:PYTHONDONTWRITEBYTECODE
try {
  $env:PYTHONDONTWRITEBYTECODE = "1"
  $scan = & python -B (Join-Path $SkillRoot "scripts\a-share-sentiment-workflow.py") scan-docx $DocxPath 2>&1
  if ($LASTEXITCODE -ne 0 -or (($scan -join "`n") -notmatch "CLEAN_PASS docx scan")) {
    throw "scan-docx failed: $($scan -join ' | ')"
  }
}
finally {
  $env:PYTHONDONTWRITEBYTECODE = $oldDontWriteBytecode
}

$resolvedDocx = (Resolve-Path -LiteralPath $DocxPath).Path
if ([string]::IsNullOrWhiteSpace($PdfPath)) {
  $PdfPath = [System.IO.Path]::ChangeExtension($resolvedDocx, ".verified.pdf")
}

$word = $null
$doc = $null
try {
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $word.DisplayAlerts = 0
  $doc = $word.Documents.Open($resolvedDocx, $false, $true)
  $pages = $doc.ComputeStatistics(2)
  $doc.ExportAsFixedFormat($PdfPath, 17)
}
finally {
  if ($doc -ne $null) { $doc.Close($false) | Out-Null }
  if ($word -ne $null) { $word.Quit() | Out-Null }
}

$postBackupOrCache = @(Get-ChildItem -LiteralPath $SkillRoot -Recurse -Force -File |
  Where-Object { $_.Name -match '\.bak|bak_' -or $_.Extension -eq '.pyc' })
if ($postBackupOrCache.Count -gt 0) {
  $names = ($postBackupOrCache | Select-Object -First 10 -ExpandProperty FullName) -join "; "
  throw "Active workflow tree contains backup/cache pollution after verification: $names"
}

[pscustomobject]@{
  status = "CLEAN_PASS"
  docx = $resolvedDocx
  word_opened = $true
  word_pages = $pages
  pdf_exported = (Test-Path -LiteralPath $PdfPath)
  pdf = $PdfPath
  scan = ($scan -join " | ")
  active_tree_backup_or_cache_count = $postBackupOrCache.Count
} | ConvertTo-Json -Compress
