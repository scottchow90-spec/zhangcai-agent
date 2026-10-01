param(
    [string]$SkillPath = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
)

$ErrorActionPreference = 'Stop'
$failures = New-Object System.Collections.Generic.List[string]

function Test-Contains {
    param(
        [string]$Path,
        [string]$Pattern,
        [string]$Message
    )
    $content = Get-Content -LiteralPath $Path -Raw
    if ($content -notmatch $Pattern) {
        $failures.Add($Message)
    }
}

$skillMd = Join-Path $SkillPath 'SKILL.md'
$openaiYaml = Join-Path $SkillPath 'agents\openai.yaml'
$refs = @(
    'references\evidence-agent-protocol.md',
    'references\research-framework.md',
    'references\risk-and-compliance.md',
    'references\memory-loop.md'
)
$scripts = @(
    'scripts\codex_entry.py',
    'scripts\run_stock_research_codex.py',
    'scripts\evidence_agent_workflow.py',
    'scripts\test_evidence_agent_workflow.py'
)

foreach ($path in @($skillMd, $openaiYaml)) {
    if (-not (Test-Path -LiteralPath $path)) {
        $failures.Add("Missing required file: $path")
    }
}

foreach ($ref in $refs) {
    $path = Join-Path $SkillPath $ref
    if (-not (Test-Path -LiteralPath $path)) {
        $failures.Add("Missing reference: $ref")
    }
}

foreach ($script in $scripts) {
    $path = Join-Path $SkillPath $script
    if (-not (Test-Path -LiteralPath $path)) {
        $failures.Add("Missing script: $script")
    }
}

if (Test-Path -LiteralPath $skillMd) {
    Test-Contains $skillMd '(?ms)^---\s*\r?\nname:\s*stock-research-codex\r?\n.*?description:\s*.{80,}?\r?\n---' 'SKILL.md frontmatter is missing name or a useful description.'
    Test-Contains $skillMd 'local Codex only' 'SKILL.md must keep the target system explicit as local Codex.'
    Test-Contains $skillMd 'Do not inspect, modify, or diagnose OpenClaw' 'SKILL.md must protect the Codex/OpenClaw boundary.'
    Test-Contains $skillMd 'fresh sources' 'SKILL.md must require fresh sources for current market facts.'
    Test-Contains $skillMd 'Decision Journal' 'SKILL.md must include a decision journal node.'
    Test-Contains $skillMd 'Self-Check And Learning' 'SKILL.md must include a self-check and learning node.'
    Test-Contains $skillMd 'references/research-framework.md' 'SKILL.md must route research tasks to the research framework reference.'
    Test-Contains $skillMd 'references/evidence-agent-protocol.md' 'SKILL.md must route multi-role work to the evidence-agent protocol.'
    Test-Contains $skillMd 'references/risk-and-compliance.md' 'SKILL.md must route action-like tasks to the risk reference.'
    Test-Contains $skillMd 'references/memory-loop.md' 'SKILL.md must route correction tasks to the memory loop reference.'
    Test-Contains $skillMd 'All roles must share one `evidence_set_id`' 'SKILL.md must require one shared evidence set.'
    Test-Contains $skillMd 'Only officially confirmed or multi-source-confirmed evidence' 'SKILL.md must keep unverified evidence out of verified synthesis.'
    Test-Contains $skillMd 'Reject order, brokerage action, trade execution' 'SKILL.md must reject trade execution output.'
    Test-Contains $skillMd 'python scripts/codex_entry\.py run -- evidence-agent smoke' 'SKILL.md must document the evidence-agent smoke command under the fixed entrypoint.'
    Test-Contains $skillMd 'python scripts/codex_entry\.py run -- evidence-agent arbitrate --evidence-file <path> --roles-file <path>' 'SKILL.md must document the evidence-agent arbitration command under the fixed entrypoint.'
}

$protocolMd = Join-Path $SkillPath 'references\evidence-agent-protocol.md'
if (Test-Path -LiteralPath $protocolMd) {
    Test-Contains $protocolMd '(?m)^- `fundamentals`$' 'Evidence protocol must define the fundamentals role.'
    Test-Contains $protocolMd '(?m)^- `market_and_technical`$' 'Evidence protocol must define the market and technical role.'
    Test-Contains $protocolMd '(?m)^- `catalyst`$' 'Evidence protocol must define the catalyst role.'
    Test-Contains $protocolMd '(?m)^- `risk`$' 'Evidence protocol must define the risk role.'
    Test-Contains $protocolMd '(?m)^- `valuation`$' 'Evidence protocol must define the valuation role.'
    Test-Contains $protocolMd 'Every role receives the same `evidence_set_id`' 'Evidence protocol must require shared evidence identity.'
    Test-Contains $protocolMd 'must not enter verified synthesis' 'Evidence protocol must exclude unverified facts from synthesis.'
    Test-Contains $protocolMd 'recursively rejects trade-execution fields' 'Evidence protocol must reject nested execution fields.'
    Test-Contains $protocolMd 'python scripts/codex_entry\.py run -- evidence-agent smoke' 'Evidence protocol must document the fixed-entry smoke command.'
    Test-Contains $protocolMd 'python scripts/codex_entry\.py run -- evidence-agent arbitrate --evidence-file <path> --roles-file <path>' 'Evidence protocol must document the fixed-entry arbitration command.'
}

$runnerPy = Join-Path $SkillPath 'scripts\run_stock_research_codex.py'
if (Test-Path -LiteralPath $runnerPy) {
    Test-Contains $runnerPy 'from evidence_agent_workflow import main as evidence_agent_main' 'Research runner must import the evidence-agent main function.'
    Test-Contains $runnerPy 'sys\.argv\[1:2\]\s*==\s*\["evidence-agent"\]' 'Research runner must dispatch the evidence-agent subcommand.'
    Test-Contains $runnerPy 'evidence_agent_main\(sys\.argv\[2:\]\)' 'Research runner must forward evidence-agent arguments.'
}

if (Test-Path -LiteralPath $openaiYaml) {
    Test-Contains $openaiYaml 'display_name:\s*"Stock Research Codex"' 'agents/openai.yaml display_name is missing or stale.'
    Test-Contains $openaiYaml 'default_prompt:\s*"Use \$stock-research-codex' 'agents/openai.yaml default prompt must mention the skill.'
}

$allSkillText = Get-ChildItem -LiteralPath $SkillPath -Recurse -File |
    Where-Object { $_.FullName -notmatch '\\scripts\\validate_stock_skill\.ps1$' } |
    ForEach-Object { Get-Content -LiteralPath $_.FullName -Raw }

if (($allSkillText -join "`n") -match '\[TODO:|TODO item|Replace with') {
    $failures.Add('Skill files still contain template TODO text.')
}

if ($failures.Count -gt 0) {
    Write-Output 'Stock Research Codex skill validation failed:'
    foreach ($failure in $failures) {
        Write-Output " - $failure"
    }
    exit 1
}

Write-Output 'Stock Research Codex skill is valid.'
Write-Output "Checked: $SkillPath"
