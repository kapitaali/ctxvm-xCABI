# RR-DSHA-CLEAR-20261116 — owner clearance for Plan A (dsh envelope/mapping fix)

The review lane asked the owner to rule on the four plans in the dsh lane's handoff 10, with Plan A
recommended. The owner's answer was one line, verbatim:

> A

That clears **Plan A only**, as recommended in `reports/RR-DSHEVENT-20261116.md`: the dsh lane may implement the
`SessionEvent` envelope fix in `packages/deepseek/**`.

## Scope of the clearance

| item | cleared? |
|---|---|
| unwrap `data` at every read site (`event-map.ts`, `tracer.ts` `ensureTracer`, `page-table.ts`) via one helper (`eventData(event) = event.data ?? event` or equivalent) | **yes** |
| convert unit fixtures/mocks to the envelope shape `{type, seq, time, data}`; keep the no-message regression | **yes** |
| assert a leading `request/header` yields real provider/model in `session.open`, and that a `tool/result` yields ≥1 `page.declare` | **yes** |
| live verification: one web/headless session, trace named with exits and date, `spec/rfc-0.1/validate_schema_v0_1.py` + `ctxvm replay`, whole test suite | **yes, required** — the fix is not done until the live trace carries identity and a page declaration |
| Plan B (schemastery peer) | **no** — deferred until A lands, or needs a separate word |
| Plan C (acceptance #4) | **no** — still held on a credential and the failed-turn 400 decision |
| Plan D (lint in another lane's file) | **no** — route to that file's owner |

Standing constraints: dsh lane owns `packages/deepseek/**` and `reports/RR-W22*`; no touch to `tools/**`, `design/**`,
other `packages/**`, `research/**`, or another lane's uncommitted work. No push — the owner pushes. Attribution
`kapitaali <teppo@kapitaali.com>`. No cost or model-output claim from a trace; private traces stay private
(law 9). No recursive delete targeting `~`, `$HOME`, `/`, or a bare home-resolving path.

## Handoff to the dsh lane

Their handoff 10 Plan A is the implementation guide; the verification bar is the bullet marked *required* above.
Stage explicit paths only via a private index; `git read-tree HEAD` on the shared index afterwards; `git-hygiene.sh`
OK. Gate: `bash tools/run-ci.sh` unpiped to a dated log with ambient `CTXVM_*` cleared, plus
`node --test packages/deepseek/test/` (expect more than 12 pass, replay skip named), `check-handoff.sh` ALL PASS.
Record the RR id, the live trace path (private, no bytes committed), validator and replay exits, and the date.

## Mechanism note

No signature artifact: the owner rules in chat and the review lane records the ruling in a file with the date and
the exact decision (precedent `RR-W8CSEQ-20261111`). If a chat summary and this file disagree, the file wins.

Written by the review lane. No source change, no model call, no pair, no spend.
