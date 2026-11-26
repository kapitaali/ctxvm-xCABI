# RR-SHADOW-LIVE-VERIFY-20261126 — 0.13.36 control shadow collection verified live

Lane: hermes. Documentation of the live verification after `RR-SHADOW-LIVE-FIX-20261126`.
Gateway pid 90481 holds 0.13.36 (`sync-plugin.sh --check`). No code, profile, gateway, model-config,
release, or push action by this card. Raw traces stay private.

## 1. Live evidence

`~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl` exists and validates:
**11 records / 3 sessions**, schema `ctxvm-shadow-selection/v1`, all `policy_applied=false`,
`request_unchanged=true`, `policy.mode=fresh`. Two sessions have flushed coverage sidecars:

| session | plugin.version | profile | shadowSelection | source | shadowSelections | engineSelections | write failures |
|---|---|---|---|---|---|---|---|
| `local-a712144a…` | 0.13.36 | w8-shadow | true | settings | 3 | 0 | 0 |
| `local-ed253cd1…` | 0.13.36 | w8-shadow | true | settings | 5 | 0 | 0 |

This is the first live proof that the **control** profile reaches the pure shadow planner through
`pre_api_request`, the by-path policy stamp attests the setting, and the observer writes valid
content-free records without invoking the ctxvm engine.

## 2. Shape finding — valid records, no would-drop pages yet

Every observed record has `floor_tokens == resident_tokens >= 24,000` and `dropped_pages == []`.
That is the L5 **floor-bust** shape: in a one-turn session the protected head/tail set is the whole
request, so the keep law cannot evict. This is not a shadow-path failure — the planner, writer,
schema, privacy and attestation all worked — but it means these records cannot nominate candidate
pins. Useful shadow data needs a multi-turn workload with an evictable middle band.

The offline join remains descriptive until such records exist; no rate or candidate pin is claimed.

## 3. Probe note

A direct CLI creation probe with `-m/--provider/-t` overrides returned rc=2 ("Resume retains gateway
session policy; creation overrides are unsupported on resume"). The existing W8 driver documents this
host limitation at `tools/w8-driver.py:170–190`; it is not a shadow defect. The authorized live
collection path produced the records above. No profile or model config was edited to work around it.

## 4. Durable private evidence

`~/.local/state/ctxvm/w8-runs/shadow-live-verify-20261126/`: snapshot `selection.jsonl` (11 records),
two coverage sidecars, `checksums.sha256`. Validator: `tools/shadow-selection-validate.py` → OK.
No raw trace or body is committed.

## 5. Limits / owed

Fresh control shadow mode only; stable control parity is not claimed. Candidate pins remain
offline-only. No causal-importance, cost-saving, paging-quality, model-quality, determinism,
availability, or redaction claim. Next data step (experiment/research lane): a multi-turn `w8-shadow`
collection with an evictable middle, then the blocked join card can run.
