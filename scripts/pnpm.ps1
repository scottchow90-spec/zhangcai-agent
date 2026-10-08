param([Parameter(ValueFromRemainingArguments=$true)][string[]]$PnpmArgs)
$ErrorActionPreference = 'Stop'
$project = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$node = Join-Path $project '.runtime/node/node.exe'
$pnpm = Join-Path $project '.runtime/tools/pnpm/bin/pnpm.mjs'
if (-not (Test-Path -LiteralPath $node) -or -not (Test-Path -LiteralPath $pnpm)) { throw 'Run scripts/bootstrap-dev.ps1 first.' }
$env:PATH = (Join-Path $project '.runtime/bin') + ';' + (Join-Path $project '.runtime/node') + ';' + (Join-Path $project '.runtime/python') + ';' + $env:PATH
$env:ZHANGCAI_PYTHON = Join-Path $project '.runtime/python/python.exe'
$env:ZHANGCAI_NODE = $node
$env:PYTHONUTF8 = '1'
$env:PYTHONIOENCODING = 'utf-8'
$env:DSH_ENTRY = Join-Path $project 'packaging/vendor/deepseek-harness/lib/bin.js'
$env:DSH_NODE = $node
$env:ZHANGCAI_RELEASE_DSH_ROOT = Join-Path $project 'packaging/staging/desktop-runtime/deepseek-harness'
$env:ZHANGCAI_RELEASE_PYTHON = $env:ZHANGCAI_PYTHON
Push-Location $project
try { & $node $pnpm @PnpmArgs; $code = $LASTEXITCODE } finally { Pop-Location }
exit $code
