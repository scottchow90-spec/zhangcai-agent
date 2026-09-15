param([string]$Label)
$p='C:\work\260907 掌财智能体\CodeX-st-wsp\zhangcai-demo\data\harness\tasks\task-449e1884-6460-492b-ba6a-dbc7611ab358.txt'
$c=Get-Content -Raw -LiteralPath $p
$idx=$c.IndexOf($Label)
if($idx -lt 0){ Write-Output "NOTFOUND $Label"; exit 1 }
for($k=$idx;$k -lt [Math]::Min($c.Length,$idx+200);$k++){ if($c[$k] -eq '[' -or $c[$k] -eq '{'){$open=$k;break} }
$i=$open; $depth=0; $inStr=$false; $esc=$false
while($i -lt $c.Length){ $ch=$c[$i]
  if($inStr){ if($esc){$esc=$false} elseif($ch -eq '\'){$esc=$true} elseif($ch -eq '"'){$inStr=$false} }
  else { if($ch -eq '"'){$inStr=$true} elseif($ch -eq '[' -or $ch -eq '{'){$depth++} elseif($ch -eq ']' -or $ch -eq '}'){$depth--; if($depth -eq 0){break}} }
  $i++ }
$o=($c.Substring($open,$i-$open+1)) | ConvertFrom-Json
if($o -is [array]){
  foreach($e in $o){
    $parts=@()
    foreach($pr in $e.PSObject.Properties){
      $v=$pr.Value
      if($v -is [array]){ $v=($v | ForEach-Object { if($_ -is [string]){$_} else { "$($_.code)/$($_.name)/$($_.pct)" } }) -join ',' }
      $parts+="$($pr.Name)=$v"
    }
    Write-Output ($parts -join "`t")
  }
} else {
  foreach($pr in $o.PSObject.Properties){ $v=$pr.Value; if($v -is [array]){ $v=($v -join ',') }; Write-Output "$($pr.Name)=$v" }
}
