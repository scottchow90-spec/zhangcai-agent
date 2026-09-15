param([string]$Label,[string]$Mode='array')
$p='C:\work\260907 掌财智能体\CodeX-st-wsp\zhangcai-demo\data\harness\tasks\task-449e1884-6460-492b-ba6a-dbc7611ab358.txt'
$c=Get-Content -Raw -LiteralPath $p
$idx=$c.IndexOf($Label)
if($idx -lt 0){ Write-Output "NOTFOUND $Label"; exit 1 }
$open=$null; $close=$null
for($k=$idx;$k -lt [Math]::Min($c.Length,$idx+200);$k++){ if($c[$k] -eq '['){$open=$k;$close=']';break}; if($c[$k] -eq '{'){$open=$k;$close='}';break} }
$i=$open; $depth=0; $inStr=$false; $esc=$false
while($i -lt $c.Length){ $ch=$c[$i]
  if($inStr){ if($esc){$esc=$false} elseif($ch -eq '\'){$esc=$true} elseif($ch -eq '"'){$inStr=$false} }
  else { if($ch -eq '"'){$inStr=$true} elseif($ch -eq '[' -or $ch -eq '{'){$depth++} elseif($ch -eq ']' -or $ch -eq '}'){$depth--; if($depth -eq 0){break}} }
  $i++ }
$json=$c.Substring($open,$i-$open+1)
$o=$json | ConvertFrom-Json
if($Mode -eq 'raw'){ Write-Output $json; exit 0 }
if($o -is [array]){ Write-Output "COUNT=$($o.Count)" } else { Write-Output ($o.PSObject.Properties | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join '; ' }
