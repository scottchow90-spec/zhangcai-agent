param(
  [string]$Source = 'electron-app\resources\zhangcai-icon.png',
  [string]$Destination = 'electron-app\resources\zhangcai-icon-256.png',
  [string]$IcoDestination = 'electron-app\resources\zhangcai-icon.ico'
)

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$sourcePath = Join-Path $projectRoot $Source
$destinationPath = Join-Path $projectRoot $Destination
if (-not (Test-Path -LiteralPath $sourcePath)) { throw "Icon source not found: $sourcePath" }

Add-Type -AssemblyName System.Drawing
$sourceBitmap = $null
$targetBitmap = $null
$graphics = $null
try {
  $sourceBitmap = [System.Drawing.Bitmap]::new($sourcePath)
  $targetBitmap = [System.Drawing.Bitmap]::new(256, 256, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)
  $graphics = [System.Drawing.Graphics]::FromImage($targetBitmap)
  $graphics.Clear([System.Drawing.Color]::Transparent)
  $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
  $graphics.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
  $graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::HighQuality
  $graphics.DrawImage($sourceBitmap, 0, 0, 256, 256)
  $targetBitmap.Save($destinationPath, [System.Drawing.Imaging.ImageFormat]::Png)
}
finally {
  if ($graphics) { $graphics.Dispose() }
  if ($targetBitmap) { $targetBitmap.Dispose() }
  if ($sourceBitmap) { $sourceBitmap.Dispose() }
}
Get-Item -LiteralPath $destinationPath | Select-Object FullName, Length

# A PNG payload inside an ICO is supported by Windows Vista and later and
# avoids the bundled icon-tool's native conversion path, which is not stable
# in this workspace. The PNG above remains the exact second supplied image,
# normalized to the standard 256x256 desktop-icon size.
$pngBytes = [System.IO.File]::ReadAllBytes($destinationPath)
$icoPath = Join-Path $projectRoot $IcoDestination
$stream = $null
$writer = $null
try {
  $stream = [System.IO.File]::Open($icoPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
  $writer = [System.IO.BinaryWriter]::new($stream)
  $writer.Write([UInt16]0)
  $writer.Write([UInt16]1)
  $writer.Write([UInt16]1)
  $writer.Write([byte]0)
  $writer.Write([byte]0)
  $writer.Write([byte]0)
  $writer.Write([byte]0)
  $writer.Write([UInt16]1)
  $writer.Write([UInt16]32)
  $writer.Write([UInt32]$pngBytes.Length)
  $writer.Write([UInt32]22)
  $writer.Write($pngBytes)
}
finally {
  if ($writer) { $writer.Dispose() }
  elseif ($stream) { $stream.Dispose() }
}
Get-Item -LiteralPath $icoPath | Select-Object FullName, Length
