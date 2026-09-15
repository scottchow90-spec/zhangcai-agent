param(
  [Parameter(Mandatory=$true)][string]$DocxPath,
  [Parameter(Mandatory=$true)][string]$PdfPath,
  [Parameter(Mandatory=$true)][string]$ResultPath
)

$ErrorActionPreference = "Stop"

function Get-Sha256Hex {
  param([Parameter(Mandatory=$true)][string]$LiteralPath)
  $stream = [System.IO.File]::OpenRead($LiteralPath)
  try {
    $hasher = [System.Security.Cryptography.SHA256]::Create()
    try {
      $bytes = $hasher.ComputeHash($stream)
      return ([System.BitConverter]::ToString($bytes)).Replace("-", "").ToLowerInvariant()
    } finally {
      $hasher.Dispose()
    }
  } finally {
    $stream.Dispose()
  }
}
$word = $null
$document = $null
$result = [ordered]@{
  schema = "A_SHARE_SENTIMENT_WORD_PROBE_V1"
  status = "BLOCKED"
  docx_path = [System.IO.Path]::GetFullPath($DocxPath)
  docx_bytes = 0
  docx_sha256 = ""
  word_opened = $false
  word_pages = 0
  pdf_exported = $false
  pdf_path = [System.IO.Path]::GetFullPath($PdfPath)
  pdf_bytes = 0
  pdf_sha256 = ""
  errors = @()
}

try {
  if (!(Test-Path -LiteralPath $DocxPath -PathType Leaf)) {
    throw "docx_missing"
  }
  $docxItem = Get-Item -LiteralPath $DocxPath
  $result.docx_bytes = $docxItem.Length
  $result.docx_sha256 = Get-Sha256Hex -LiteralPath $DocxPath
  $pdfDirectory = [System.IO.Path]::GetDirectoryName([System.IO.Path]::GetFullPath($PdfPath))
  if (!(Test-Path -LiteralPath $pdfDirectory)) {
    [System.IO.Directory]::CreateDirectory($pdfDirectory) | Out-Null
  }
  if (Test-Path -LiteralPath $PdfPath -PathType Leaf) {
    Remove-Item -LiteralPath $PdfPath -Force
  }
  $word = New-Object -ComObject Word.Application
  $word.Visible = $false
  $word.DisplayAlerts = 0
  $document = $word.Documents.Open([System.IO.Path]::GetFullPath($DocxPath), $false, $true)
  $result.word_opened = $true
  $result.word_pages = [int]$document.ComputeStatistics(2)
  $document.ExportAsFixedFormat([System.IO.Path]::GetFullPath($PdfPath), 17)
  $document.Close($false)
  $document = $null
  $word.Quit()
  $word = $null
  if (!(Test-Path -LiteralPath $PdfPath -PathType Leaf)) {
    throw "pdf_export_missing"
  }
  $pdfItem = Get-Item -LiteralPath $PdfPath
  $result.pdf_exported = $true
  $result.pdf_bytes = $pdfItem.Length
  $result.pdf_sha256 = Get-Sha256Hex -LiteralPath $PdfPath
  if ($result.word_pages -lt 1 -or $result.word_pages -gt 50) {
    throw "word_page_count_out_of_range"
  }
  if ($result.pdf_bytes -lt 20000) {
    throw "pdf_export_too_small"
  }
  $result.status = "PASS"
} catch {
  $result.errors += [string]$_.Exception.Message
} finally {
  if ($document -ne $null) {
    try { $document.Close($false) } catch {}
  }
  if ($word -ne $null) {
    try { $word.Quit() } catch {}
  }
  $resultDirectory = [System.IO.Path]::GetDirectoryName([System.IO.Path]::GetFullPath($ResultPath))
  if (!(Test-Path -LiteralPath $resultDirectory)) {
    [System.IO.Directory]::CreateDirectory($resultDirectory) | Out-Null
  }
  $json = $result | ConvertTo-Json -Depth 5
  [System.IO.File]::WriteAllText(
    [System.IO.Path]::GetFullPath($ResultPath),
    $json,
    [System.Text.UTF8Encoding]::new($false)
  )
}

$result | ConvertTo-Json -Depth 5
if ($result.status -ne "PASS") { exit 2 }
