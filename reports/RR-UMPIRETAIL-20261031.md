# RR — UMPIRETAIL — 20261031

**Card executed:** the RFC-0.1 cross-repo tail — umpire's adoption of the profile this repo
approved at D4 (2026-10-30). **Date:** 2026-10-31.
**Nature:** the work landed in the consumer repo (`kapitaali/umpire`, commits `d8ecef4`
card + `a701072` review). **No byte of this repo changed**: `spec/**`, `rust/**`,
`corpus/**`, packages, gates and counts are untouched.

## What was done (in umpire, by reference)

- **R0** — `session.open` declares `schemaVersion:"0.1"` in `spec/make_fixtures.py`,
  both `session.open` constructions in `harness/umpire.py`, and as a P4 assertion in
  `harness/test_m1.py`.
- **R1** — a deliberate re-decide emits `page.fault source:"intentional_rerun"` instead
  of `tool_recall`. `tool_recall` means "the page had been paged out and was re-fetched";
  umpire pages nothing out, so the old source misdescribed its own behaviour.
- **Consumer validator** — `spec/validate_ledger.py` L4 is version-branched: a ledger
  without `schemaVersion` keeps the strict `tool_recall`-only rule; a `"0.1"` ledger
  admits the typed source. Two engineered negatives added (`intentional_rerun` without the
  boundary; unknown `schemaVersion`) → 12/12 becomes 14/14.
- **Vendored schema** — re-vendored from this repo at `36cec7c`
  (`spec/rfc-0.1/x-cabi.schema-v0.1.json`), verbatim except a provenance `$comment`. The
  previous copy was a reorganized `$defs` fork of the v0 schema; that fork is gone.
- **Fixtures** — four migrated (ab-demo, intent-router, live-demo, support-triage) with
  page-table baselines re-derived; expected-diff audit: per ledger exactly line 1 gains
  `schemaVersion` and the fault rows retype (3/2/1/1), nothing else, records
  byte-unchanged. A new `spec/migrate_rfc01.py` is the auditable migration path.
- **Review** — a measured state review (`umpire reports/RR-REVIEW-20261031.md`) recorded
  its open queue and fixed two `.gitignore` defects: `tests/` had been ignored while
  holding nine tracked gate artifacts, and the `research/` line matched nothing because an
  inline `#` is not a comment.

## Verification (this repo's tools, on umpire's verbatim ledgers)

```
$ rust/target/release/replay ~/Documents/umpire/fixtures/ab-demo.ledger.jsonl
  before: events 6, divergences [], violations 3× faultOfResidentPage
  after:  events 6, divergences [], violations []

$ replay × 4 fixtures → ab-demo 6 / intent-router 7 / live-demo 5 / support-triage 5
  every one: divergences 0, violations 0

$ venvs/odps/bin/python spec/rfc-0.1/validate_schema_v0_1.py <4 ledgers>
  OK: all checks passed

$ git diff --stat spec/rfc-0/ 02-xcabi-events-v0.md spec/rfc-0.1/ rust/
  (empty — sealed surfaces untouched by the tail)
```

umpire's own gates after the migration: fixtures PASS 207 checks (negatives 14/14), four
`--replay` roundtrips BYTE-IDENTICAL, calibration corpus 905/945 checks and v3
2505/2625, unittests 7 + 16 + 2 OK, checksums 9/9 OK each, `build_hub.sh check`
byte-identical (packaging pins no fixture bytes — verified, not assumed).

## Semantics recorded

- The friction RFC-0.1 was written for is now measurably gone: the same six-event A/B
  ledger that produced three `faultOfResidentPage` rows produces zero, and the rows are
  the *only* thing that changed semantically.
- **The version branch is the load-bearing part.** A ledger without `schemaVersion` still
  cannot use `intentional_rerun`: the negative corpus proves the rejection, so adoption
  did not quietly widen v0.
- umpire's calibration corpora were **deliberately left v0**. Their hashes are the
  calibration of record (v3 `25b073cbc…`, referenced by the hub and the packaging
  product); re-minting would break provenance, and a v0 ledger is a true statement about a
  capture that predates the field.
- `latencyMs`/`turn` on `page.declare` were **not** adopted by umpire: its ledger carries
  no declaration turn and it measures decision latency in its *records*, not in xCABI.
  Adding them would have been invention, not adoption.

## Deviations / discoveries

- **Discovery, consumer side:** two standing fault-source negatives were vacuous — built
  on hand-made fault hashes, they failed on the join and minting rules rather than on L4,
  so they would have stayed red with L4 regressed. Both now use the real response hash and
  fail for exactly one reason.
- **Deviation, consumer side:** no unknown-version branch was added to its validator,
  because its vendored schema pins `const: "0.1"` — a branch there would be unreachable
  dead code. The negative case proves the schema rejects it instead.
- Both are recorded in umpire's own report rather than here; this card carried no
  deviation from its own scope.

## Open questions

- Whether umpire's Hermes integration (668 untracked lines, two drifted MCP servers) is
  in-scope for umpire or its own product — the same shape as D2. Ranked first in umpire's
  `RR-REVIEW-20261031.md` §5; it needs an owner decision, not another agent.

## Status

DONE. The RFC-0.1 chain is closed end to end: this repo encodes it (R0–R5 + engine), the
consumer adopts it, and the friction it was written for is gone under measurement.
Counts here are unchanged (`ts 20 + 58 + 45` / `python 91 + 44 + 8`); ALL GATES GREEN.
