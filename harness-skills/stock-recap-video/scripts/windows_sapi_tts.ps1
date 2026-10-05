param(
    [Parameter(Mandatory = $true)][string]$InputFile,
    [Parameter(Mandatory = $true)][string]$OutputFile,
    [string]$Voice = 'Microsoft Huihui Desktop',
    [ValidateRange(-10, 10)][int]$Rate = 0
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$text = Get-Content -Raw -Encoding UTF8 -LiteralPath $InputFile
if ([string]::IsNullOrWhiteSpace($text)) { throw 'Narration text is empty' }
$outputParent = Split-Path -Parent $OutputFile
if ($outputParent) { New-Item -ItemType Directory -Force -Path $outputParent | Out-Null }
$synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
try {
    $available = @($synth.GetInstalledVoices() | Where-Object { $_.Enabled } | ForEach-Object { $_.VoiceInfo.Name })
    if ($Voice -notin $available) { throw "Requested voice is unavailable: $Voice" }
    $synth.SelectVoice($Voice)
    $synth.Rate = $Rate
    $synth.Volume = 100
    $synth.SetOutputToWaveFile($OutputFile)
    $synth.Speak($text)
}
finally {
    $synth.Dispose()
}
if (-not (Test-Path -LiteralPath $OutputFile)) { throw 'SAPI did not produce an audio file' }
