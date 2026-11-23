# RR-PARTC-AUTH-20261123 — owner authorizes Part C (recoverable stub) as a fix for a measured defect, routed to hermes lane

Owner ruling 2026-11-23, verbatim: **"authorize part C"** — after the decision table's branch was literally satisfied:
Part B measured middle accuracy 8/8 → 1/8 with head 8/8 control (`RR-PARTB-RESULT`) and **0/8 post-question re-reads**
from capture bytes (`RR-PARTB-REREAD`). This is a **fix for a measured defect**, not a continuation of the paging
hypothesis. Review lane, verify-then-record. The implementation is a hermes-lane plugin change
(`packages/hermes/**`, `handoff/LANES.md:12`); I do not write it.

## 1. The five conditions (verbatim substance)

1. **New arm, not a default change.** Add a stub arm to the same Part B harness — same frozen planted-code bank,
   same scorer, same profiles, 8 sessions. Stub behavior **opt-in via a profile setting**, never on by default
   (D6/D14 consent, D17 held). Captures must attest the setting.
2. **Stub must not leak the gold.** Name + arguments + "re-run to restore" only — no value, no code. Verify with the
   dq scanner before any session.
3. **Close the UNVERIFIED gap.** With a stub present, re-read becomes directly observable as a `read_file` tool call
   on the needle file after the final question (trace evidence, independent of the fault counter). Add that readout
   so Part C resolves the half Part B could not.
4. **Standard plugin hygiene:** version bump both places, sync installed copy, gateway restart owed to operator
   (not the agent), own RR card + LOG row, no push. Keep Part B's result untouched — no re-score, no pooling.
5. **Claim ceiling stays:** no cost saving, no general paging-quality claim; one shape, one budget, one route.

## 2. Routing

Hermes lane owns `packages/hermes/**` and the installed plugin copy. The implementation surface is the stub seam in
`context_engine.py::_assemble` (`:958`): replace a dropped tool-result page with a short recoverable stub when the
profile setting is on. The setting must be captured so a sidecar attests it. The review lane records rulings and
verifies artifacts; it does not write the plugin. No owner action on the gateway is taken by any agent — restart is
owed to the operator.

## 3. What is not authorized

No default-on change, no D17 release action, no registry/catalog, no push, no re-score of Part B, no pooling with
E0/E1/E2/M1/M2/M3. Part C is measured only within the frozen Part B shape; a positive result would validate the
recovery mechanism for that shape, not prove paging helps generally.

## 4. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261123.md`. A routing
note to the hermes lane is included in the card body (§2).
