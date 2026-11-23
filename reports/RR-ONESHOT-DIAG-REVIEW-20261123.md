# RR-ONESHOT-DIAG-REVIEW-20261123 — verified: oneshot DOES flush; the stub-arm evidence gap is naming + retention, not a plugin bug

Review lane, verify-then-record. Subject: `a912c4e` (diagnostic card `reports/RR-ONESHOT-DIAG-20261123.md`) and
`39b327e` (PROJECT-STATE delta). Owner authorized the diagnostic. $0, no model call by this lane, no push.

## 1. Verified from disk

| claim | check | result |
|---|---|---|
| diagnostic card + commits landed | `git log`, `ls` | `a912c4e`, `39b327e`, card present (4,170 B) |
| `session_end` fires on `--oneshot` and `_flush_traces()` runs | `hooks-witness.log` | multiple `session_end -> flush all tracers` and `flush …jsonl bytes=… session=…` lines in the diagnostic window |
| coverage sidecars written at 0.13.30 | read the two fresh sidecars | `version: 0.13.30`, `harnessVersion: 0.23.3`, `stubDropped: off`, `arm: control` — the controlled oneshot (control profile) flushed full sidecars |
| retention at cap | trace dir count + witness | exactly **200** `.jsonl`; `retention deleted=1/2 files (max=200, days=30)` lines |
| no `recoverable` sidecar on disk | grep coverage sidecars | **none** with `stubDropped: "recoverable"` anywhere — the arm's attestation cannot be recovered |
| card's field-name shorthand | — | the card says "pluginVersion 0.13.30"; the actual coverage field is `plugin.version` (verified 0.13.30). Shorthand only; not a factual error |

**Core finding confirmed:** the "oneshot doesn't flush" premise (which I originally raised and the hermes lane adopted)
is **falsified** by the witness log — `session_end` fires, flush runs, sidecars are written. The arm's evidence gap
is capture **identity** (host names by gateway `local-*`/timestamp IDs, not the driver's `-c` name) plus **retention**
(200-file cap, 168 oneshot invocations × re-flush/prune) — both outside the flush path. No plugin fix is justified;
adding a flush hook would be a hack against naming/retention.

## 2. Ownership and scope

Hermes-lane diagnostic; I wrote none of it. No plugin change, version bump, restart, or re-score of Part C's arm.
Part C's accuracy contrast (1/8 → 7/8, head 8/8) stands untouched; the attestation gap remains recorded as such in
`RR-PARTC-ARM-RESULT`. The owner's two options (recover forward vs accept the gap) remain open — neither is a
review-lane action.

## 3. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`.
