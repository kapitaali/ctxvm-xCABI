# RR-SHADOW-LIVE-ACCEPT-20261126 — 0.13.37 persists a real would-drop page

Lane: hermes. Date 2026-11-26. Scope: live acceptance for
`RR-SHADOW-DATA-FIX-20261126`. One fresh control-shadow session on `w8-shadow`.

## 1. What was done

- Confirmed gateway pid **255162** started after the 0.13.37 files and holds the build
  (`tools/sync-plugin.sh --check`).
- Ran one anonymous one-shot session with the existing profile settings:
  `context.engine=compressor`, `budgetTokens=24000`, `shadowSelection=true`.
- Model/provider: `tencent/hy4-flash:free` / `nous`. Host: Linux x86_64.
  Sample size: one session, six shadow records. Hosted output is not deterministic;
  no seed or interval applies to this acceptance check.
- Workspace: two 57,620-byte files followed by three 25-byte files. The prompt required
  sequential `read_file` calls and marker recall.
- No profile, gateway, or model configuration was edited.

## 2. Result

Session `local-e3ab387683866946ff2a7af2cf13fdda2e2b9ae62f33148f825b3ae9ab51c3bc`:

| check | result |
|---|---|
| command exit | 0, 38.8 s |
| plugin | 0.13.37, harness 0.23.4 |
| profile / mode | `w8-shadow`, control, fresh |
| shadow selections | 6 |
| persisted drop records | 1 |
| persisted dropped pages | 1 |
| drop shape | floor 17,195 < budget 24,000 < resident 33,181 |
| dropped tokens | 15,975 |
| per-session write failures | 0 |
| process write failures | 0 |
| engine selections | 0 |
| trace digest | `1c0747d3730595dc4cc9035f4edd947562b51a46aa48bb828c67f0a57c52ccd8` |

The persisted PageId matches a declared/rendered PageId in the same trace. This closes
the live acceptance condition in `RR-SHADOW-LIVE-DATA-REVIEW-20261126`: the exact-hash
join now writes a real would-drop record instead of discarding it.

## 3. Verification commands and output

```text
python3 tools/shadow-selection-validate.py ~/.hermes/profiles/w8-shadow/ctxvm-shadow/selection.jsonl
shadow schema: OK (71 records)

python3 tools/coverage_check.py <trace> <coverage>
coverage_check: consistent (...jsonl, 8 events, digest ok)

rust/target/release/replay <trace>
{"events":8,"divergences":[],"violations":[]}

python3 spec/rfc-0.1/validate_schema_v0_1.py <trace>
OK: all checks passed
```

Durable private evidence:
`~/.local/state/ctxvm/w8-runs/shadow-live-accept-20261126/`, including `validation.json`,
`run.json`, `run.out`, `run.err`, `snapshot/`, and `snapshot.sha256`.

## 4. Deviations

None from the acceptance condition. The run used the known-working anonymous one-shot
path; named `--create-if-missing` creation overrides remain a separate host limitation.

## 5. Discoveries

- A dotted basename can yield an empty engine identity-token set; the exact historical
  `ref|contentHash` is sufficient when unique.
- The sidecar now separates session failures from the process total, so unrelated
  sessions no longer inherit an old failure.
- One accepted record is enough to unblock the offline join implementation, but not to
  estimate rates or nominate candidate pins.

## 6. Limits / next step

No causal, cost-saving, paging-quality, model-quality, determinism, availability, or
redaction claim. Raw traces remain private. Candidate pins remain offline-only. The
research/experiment lane can now implement the blocked join against fresh 0.13.37 data;
no rates or pins are computed in this card. No publish or push.
