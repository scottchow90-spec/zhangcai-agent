param(
    [Parameter(Mandatory = $true)]
    [string]$WavePath,
    [Parameter(Mandatory = $true)]
    [string]$ExpectedScript
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$culture = [System.Globalization.CultureInfo]::GetCultureInfo('zh-CN')
$engine = [System.Speech.Recognition.SpeechRecognitionEngine]::new($culture)
try {
    $rawExpected = Get-Content -LiteralPath $ExpectedScript -Raw -Encoding UTF8
    $phrases = @($rawExpected -split '[。！？!?；;]' | ForEach-Object { $_.Trim().Trim('，', ',') } | Where-Object { $_ })
    if ($phrases.Count -eq 0) { throw 'Expected script does not contain a recognizable phrase' }
    $choices = [System.Speech.Recognition.Choices]::new()
    $choices.Add([string[]]$phrases)
    $builder = [System.Speech.Recognition.GrammarBuilder]::new($choices)
    $builder.Culture = $culture
    $engine.LoadGrammar([System.Speech.Recognition.Grammar]::new($builder))
    $engine.SetInputToWaveFile((Resolve-Path -LiteralPath $WavePath).Path)
    $segments = @()
    while ($true) {
        try {
            $result = $engine.Recognize()
        }
        catch [System.InvalidOperationException] {
            if ($_.Exception.Message -like '*No audio input*') { break }
            throw
        }
        if ($null -eq $result) { break }
        $segments += [pscustomobject]@{
            text = $result.Text
            confidence = [math]::Round($result.Confidence, 4)
        }
    }
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
    [pscustomobject]@{
        status = if ($segments.Count -gt 0) { 'PASS' } else { 'FAIL' }
        recognizer = $engine.RecognizerInfo.Description
        expected_phrases = $phrases
        segments = $segments
    } | ConvertTo-Json -Depth 4
}
finally {
    $engine.Dispose()
}

