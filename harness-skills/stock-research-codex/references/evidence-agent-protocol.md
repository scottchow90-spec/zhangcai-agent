# Evidence-Agent Protocol

## Purpose

This protocol adapts useful research patterns from TradingAgents,
TradingAgents-CN, and ai-hedge-fund without importing their execution layers.
It adds bounded role separation, a shared evidence set, and deterministic
arbitration to the existing evidence-first research workflow.

It is a research and decision-support protocol only. It must not connect to a
broker, construct an executable order, or initiate automated trading.

## Shared Evidence Set

Build one evidence set before role analysis. Every evidence item must contain:

- `evidence_id`
- `claim`
- `source`
- `source_url`
- `observed_at`
- `verification_status`
- `source_rank`

Every role receives the same `evidence_set_id`. A role may cite only evidence
IDs that exist in that set. Unknown evidence IDs and missing required fields
are protocol errors.

## Bounded Roles

The only supported roles are:

- `fundamentals`
- `market_and_technical`
- `catalyst`
- `risk`
- `valuation`

Each role output must contain its role, conclusion, cited evidence IDs,
confidence, risks, and unverified items. Role separation is an analysis aid;
it is not permission to create independent facts or use different hidden
evidence.

## Evidence Rules

- A conclusion with no cited evidence is degraded and capped at `0.2`
  confidence.
- Only `official_confirmed` and `multi_source_confirmed` evidence may support
  factual synthesis.
- Single-source, stale, pending, disputed, or otherwise unverified evidence
  remains in `unverified_items`; it must not enter verified synthesis.
- Explicit contradictions and opposing stances on the same topic must be
  listed in `conflicts`.
- Final confidence is constrained by role confidence, verified evidence
  coverage, unresolved conflicts, and unverified items.

## Arbitration Output

The arbitration result contains:

- `evidence_set_id`
- `synthesis`
- `supporting_evidence_ids`
- `conflicts`
- `confidence`
- `risks`
- `unverified_items`
- `decision_criteria`

The synthesis is not a trade instruction. It records only conclusions backed
by verified evidence and identifies the conditions that would change the view.

## Execution Boundary

The protocol recursively rejects trade-execution fields, including:

- `order`
- `orders`
- `broker_action`
- `execute_trade`
- `place_order`
- `trade_execution`
- `auto_trade`
- `automated_trade`

Do not weaken this boundary by renaming an order field or embedding execution
instructions inside a nested object. Position sizing, brokerage credentials,
gateway configuration, and live-trading integration remain outside this
skill.

## Fixed Entrypoint

Run the protocol only through the skill's existing `codex_entry.py`:

```powershell
python scripts/codex_entry.py run -- evidence-agent smoke
python scripts/codex_entry.py run -- evidence-agent arbitrate --evidence-file <path> --roles-file <path>
```

`evidence-agent` is a subcommand under the original `run --` contract. It is
not a second public entrypoint, and normal skill execution must not call
`evidence_agent_workflow.py` directly.

## Verification

Run:

```powershell
python scripts/test_evidence_agent_workflow.py
```

The tests must prove shared evidence identity, role schema enforcement,
evidence citation integrity, no-evidence degradation, verified-only synthesis,
conflict reporting, confidence constraints, and rejection of execution fields.
