$probeValue = '.runtime\node\node.exe'
Write-Output ("probe=[" + $probeValue + "]")
Write-Output ("exists=" + (Test-Path -LiteralPath $probeValue))
