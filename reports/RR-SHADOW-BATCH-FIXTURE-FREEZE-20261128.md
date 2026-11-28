# RR-SHADOW-BATCH-FIXTURE-FREEZE-20261128 — research ratified the fixture/prompt freeze

Review/experiment handoff. Date: 2026-11-28.
No live model call, session creation, gateway/profile/config change, restart, pin activation, publish, or push.

## 1. Ratification

Research/experiment ratified the operator-authorized draft without amendment. The frozen artifact keeps
the private name `shadow-fixture-draft-20261128-v1` for byte identity; its status is now FROZEN, not draft.

- Manifest SHA-256: `202b9468ffa53301e7b56e29a2df92a3074c47ecb1a5f4164c50f820acdbc735`
- Generator SHA-256: `3c72e83e79e53374574df24889c32cef956874d4789cf17f517983663782f541`
- Seed: `20261128`
- Freeze record: `design/experiment-runs/SHADOW-BATCH-FIXTURE-FREEZE-20261128.md`

## 2. Revalidated inputs

```text
sha256sum -c checksums.sha256  -> 12/12 OK
collector load_fixtures         -> 3/3 shapes valid
directory modes                 -> 0700
file modes                      -> 0600
```

The pressure workspace remains two 57,600-byte files plus three 192-byte tails. The dependency
workspace remains A 57,600 / B 57,600 / C 28,800 bytes plus a 192-byte tail with explicit A→B→C
references. Exact prompt hashes are recorded in the freeze document.

## 3. Execution status

The collector is accepted at `7c53889`; the fixture/prompt freeze is now ratified. The remaining
pre-execution gate is a fresh successful preflight against the active 0.13.37+ gateway. The authorized
limits remain at most 18 attempts, at most six per shape, stopping at 12 informative sessions.

No live batch has started in this card. No metric, rate, candidate pin, causal, cost-saving, paging-quality,
model-quality, determinism, availability, redaction, or safety claim is produced.

## 4. Applied

This report, the freeze document, one four-pipe `reports/LOG02.md` row, one `reports/RR-DAY-20261128.md`
section, and a separate PROJECT-STATE delta. Private fixture bytes remain outside git. No push.
