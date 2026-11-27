# RR-SHADOW-COLLECTOR-PROPOSAL-20261127 — tracked batch collector + 12-session varied corpus proposed

Review/experiment lane. Date 2026-11-27. No implementation, model call, spend, gateway/profile change, or push.

## Proposal

Created `design/experiment-runs/SHADOW-BATCH-COLLECTOR-20261127.md`, the recommended highest-leverage next card:

- tracked `tools/collect-shadow.py` with fail-closed preflight;
- three frozen workload shapes: read-once pressure, deliberate later re-read, dependency chain;
- 12 valid informative sessions, four per shape, maximum 18 attempts;
- immediate private snapshots and gate receipts per session;
- automatic offline join and stop at the requested valid count;
- aggregate-only committed output.

Baseline corrected to current HEAD `7487bcc`: join OK at n=9, 107 records, 42 selections, 9 drops, no later reuse,
no pins. Only one varied session was informative.

## Authorization needed

Owner rulings are required for:

1. routing implementation to the hermes/tools lane;
2. up to 18 live free-model calls under the frozen quota/stop rules;
3. the three shapes and 12-session target.

No worktree pilot, reviewer-cadence change, close-card automation, CI tuning, or cold-start rewrite is bundled
into this card. Those remain separate process decisions.

## Applied

This card, the run plan, one four-pipe LOG02 row, a day-file section, and a PROJECT-STATE next-action update.
