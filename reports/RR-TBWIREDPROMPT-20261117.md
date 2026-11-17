# RR-TBWIREDPROMPT-20261117 — the smoke-authorization prompt, committed at the owner's request

At the owner's request ("commit it, it's running now") this card records **verbatim** the prompt I handed them
to start the wired experiment. It was written 2026-11-16, after the budget ruling `53cf208`, and authorized the
**one-prompt compatibility smoke only**, with a STOP before the full run.

**Status note, recorded before anything else:** when I came to commit it, the smoke had already landed
(`d112a7f`, `RR-TBOPENSMOKE-20261116`: v2.3.0 PASS, tool domain unexercised at runtime) and the full run had been
authorized separately under a freshly preregistered ceiling of **198** (`5dd1727`, `TB-WIRED-BLOCK-20261117`).
Those later records govern. This card is the verbatim handoff text, not a claim about the running experiment,
and does not re-authorize anything.

## The prompt, verbatim

```
Wired OpenCode T-B: run the compatibility smoke, then STOP

Owner authorization 2026-11-16: the wired experiment starts with the one-prompt compatibility smoke only. The full 193-prompt run is not authorized by this prompt.

Read first: AGENTS.md; handoff/LANES.md; the plan of record design/TB-OPENCODE-WIRED.md (esp. §§2–5, 9); reports/RR-TBOPENWIRE-PLAN-20261116.md; reports/RR-TBWIRED-20261116.md (the four offered deltas); reports/RR-TBWIRED-REVIEW.md; reports/RR-TBBREACH-20261116.md (the breach ruling); reports/RR-TBBUDGET-20261116.md.

Settled — do not re-litigate:
- The unwired full run is a BREACH (582 requests vs the frozen 579). No retroactive ceiling, no clean-cell re-score, no GO for a Hermes paged cell from it. 579 and 451 are void; 582 is an observation, not a ceiling.
- CTXVM_BUDGET_TOKENS = 60000 (owner ruling RR-TBBUDGET-20261116), with the note that in this mirror-only adapter the field is metadata and drives headroom only — not an engine budget.
- design/TB-OPENCODE-WIRED.md is the plan of record. The other lane's card was withdrawn as a duplicate; its verification and deltas are kept in RR-TBWIRED-20261116.md.

Your task: execute §5 of the plan, nothing more.
1. Create the shim inside a fresh private run dir only (e.g. ~/.local/state/ctxvm/w8-runs/tb-wired-smoke-<id>/.opencode/plugins/ctxvm.ts), re-exporting the adapter's default {id, setup} from the absolute path to packages/opencode/live/ctxvm.ts. No built dist, no config-key shortcut.
2. Set the seven env vars in the process that boots OpenCode: CTXVM_TRACE_DIR (private state dir), a fresh CTXVM_TRACE_NAME, CTXVM_MODEL=opencode-go/hy4-flash-free, CTXVM_PROVIDER=opencode-go, CTXVM_AGENT_ID, CTXVM_BUDGET_TOKENS=60000, CTXVM_OPENCODE_VERSION="$(opencode --version)". Enumerate and unset ambient CTXVM* first, then set these deliberately.
3. Run one short prompt (Reply with the single word OK and nothing else.) with opencode run --standalone --auto so tools remain available. Let the process exit gracefully — a hard kill loses the flush silently and is not evidence.
4. Verify all five smoke conditions from plan §5: exit 0 with a reply; <name>.jsonl and <name>.meta.json written under CTXVM_TRACE_DIR; hooks-witness.log shows the complete flush chain across both hook domains; python3 spec/rfc-0.1/validate_schema_v0_1.py <trace> exit 0; ./rust/target/release/replay <trace> exit 0 with divergences: []. Also confirm session.open carries the real provider/model, and that meta.json has pluginVersion / harnessVersion / opencodeVersion populated rather than null.

Fold these into the smoke record (they are accepted deltas):
- Key every reply on the prompt's own fixture/data-NN.csv reference, never the turn index. The prompt list is lexicographic — P100 asks for data-181.csv.
- The auth detector matches explicit forms only (HTTP 401/429, insufficient_credits, FreeUsageLimitError, authentication_error). Never bare digits: 401 once matched inside the data value 8401 and stopped a run.
- State the full-run fidelity pass criteria in the smoke report (≥192 distinct page refs in page.declare, one real-identity session.open, populated meta fields, witness across hook domains, completeness scores re-derived from the same replies). Do not run them yet.
- After the smoke, measure the call rate and preregister a fresh ceiling before the full run. The ceil(193 × r_smoke × 1.10) + 5 formula in the delta card is a proposal, not a measurement; the plan's authoritative rule is ceil(193 × r_smoke) plus a separately stated P193 allowance. Freeze one integer, state its derivation, and record any overrun rather than repairing it.

STOP after the smoke. Report: verdict (PASS or FAILED — v2.3.0 compatibility is the question), trace and meta paths (private, no bytes committed), validator and replay exits with the full JSON, hooks-witness.log summary, meta field values, call count, and cost — labelled harness-reported, not a receipt, with no cost claim. Return the exact authorization sentence needed for the full run. Do not start the 193-prompt run, do not freeze a ceiling in a committed card without the new prereg, do not create a shim anywhere else, do not edit packages/** or tools/**.

Repo rules: explicit staged paths via a private index; git read-tree HEAD on the shared index afterwards; run bash tools/git-hygiene.sh before staging shared files — a previous lane left a stale index with staged deletions. LOG rows append-only with exactly four pipes. Never push. Attribution kapitaali <teppo@kapitaali.com>. No trace bytes, credentials, or unredacted session text in any repo file (law 9). Never suggest or type a recursive delete targeting ~, $HOME, /, or a bare home-resolving path.

Gates for the smoke: bash tools/check-handoff.sh -> ALL PASS; repo gate unchanged by a smoke, but re-run bash tools/run-ci.sh unpiped with ambient CTXVM_* cleared if you change any tracked file.
```

## Note on the one gap the smoke could not close

The prompt required witness evidence "across both hook domains". The smoke card reports that the
one prompt made **no tool call**, so `tool.execute.before/after` were registered in source but not exercised at
runtime; `hookStats` shows `before: 0, after: 0`. That is recorded as a full-run fidelity item in
`RR-TBOPENSMOKE-20261116` and `TB-WIRED-BLOCK-20261117` §3 (D1). This card does not change it.

No code change, no model call, no spend.
