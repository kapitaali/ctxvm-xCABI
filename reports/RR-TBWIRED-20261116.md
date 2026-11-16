# RR-TBWIRED-20261116 — the wired plan was already landed by the opencode lane; this card is the delta

**Disposition: my plan is withdrawn as a duplicate.** While this lane was writing `design/TB-WIRED-PLAN.md`,
the opencode lane landed `d06cf06` — *Plan the wired OpenCode T-B run, stop before the smoke*
(`RR-TBOPENWIRE-PLAN-20261116`) — with its own proposal card `design/TB-OPENCODE-WIRED.md`. That commit also
carried this lane's LOG row and day section, because the shared files were dirty with them at the time. Per
`handoff/LANES.md` ("another lane can land the card you are writing mid-session — read theirs first and drop
yours rather than double-land it"), my duplicate card is deleted and **`design/TB-OPENCODE-WIRED.md` is the plan
of record** for the wired run.

Nothing was executed: no model call, no shim in a live run directory, no edit under `packages/**` or `tools/**`.

## 1. Their card, checked independently

I verified the five facts the plan rests on, from the files rather than from the card:

| claim | how | result |
|---|---|---|
| the adapter exports the module shape the shim relies on | `grep -n "export default\|id:\|setup" packages/opencode/live/ctxvm.ts` | `:208 export default`, `:209 id: "ctxvm-live"`, `:210 async setup(ctx)` |
| the project-local shim is the documented surface | `packages/opencode/live/README.md:8-10` | `<session-project>/.opencode/plugins/ctxvm.ts` re-exporting the source path |
| the adapter is inert without the trace dir | `ctxvm.ts:17, 235` | "INERT unless `CTXVM_TRACE_DIR`" |
| every env var in their §3 is actually read | `grep -n "CTXVM_" ctxvm.ts` | dir `:211`, name `:227`, budget `:172` (default 200000), model `:312`, provider `:313`, agent `:315`, version `:136` |
| v2.3.0 compatibility is genuinely unknown | `README.md:35, 104, 113` vs `opencode --version` | contract notes stop at v2.1.2/v2.1.3 (+ v2.1.4 erratum); installed **v2.3.0** ⇒ UNVERIFIED |

So the plan's mechanics and its one blocking unknown are correct as written.

## 2. Four deltas their card does not state — offered to its owner, not applied

**D1 — the full run needs explicit fidelity pass criteria, not only smoke criteria.** Their §5 gates the smoke;
§7 names the claim but not what makes the run's traces adequate. The check I would add: `page.declare` rows
covering **≥ 192 distinct file refs**, one `session.open` naming the real model and provider, `.meta.json` with
`pluginVersion` / `harnessVersion` / `opencodeVersion` populated rather than `null`, `hooks-witness.log` showing
**both** hook domains across the run rather than only at init, and the completeness scores re-derived from the
same replies — unchanged, or the difference explained.

**D2 — the ledger must key on each prompt's own file reference.** Their §1 records the lexicographic defect as
settled; the wired driver needs the rule, because it will hit the same trap: the prompt list is `data-01`…`09`,
`10`, `100`…`109`, `11`…, so **turn 100 asks for `data-181.csv`**. Parse each prompt's `fixture/data-NN.csv` and
key the reply on it, never on the turn index.

**D3 — the auth detector must match explicit forms only** (`HTTP 401/429`, `insufficient_credits`,
`FreeUsageLimitError`, `authentication_error`), never bare digits: the first driver stopped on `401` inside the
data value `8401`.

**D4 — the ceiling rule can be made arithmetic.** Their §6 states `ceil(193 × r_smoke)` plus a separately
stated allowance for P193 if the smoke does not exercise a reconciliation-shaped prompt. The measured allowance
is **5 requests** (P193 took the count 577 → 582), so the concrete form is:

```
ceiling = ceil(193 × r_smoke × 1.10) + 5
```

and the alternative is to include one reconciliation-shaped prompt in the smoke, which removes the allowance but
not the 10 % margin. Either way the integer is frozen before the run and an overrun is recorded, never repaired.

## 3. One disagreement that needs a ruling, not a default

`CTXVM_BUDGET_TOKENS`: their §3 sets **200000** and says correctly that it is the adapter's `headroom` field
only, not an engine budget. My withdrawn card set **60000**, T-B's declared budget. Both are defensible; they
differ in what a reader of the `.meta.json` later sees. My reading: for a capture-fidelity run, the recorded
budget should be the budget the design declares, so a later reader is not misled by a 200000 that no arm ever
had — with the comment that the field drives `headroom` only. Their lane owns the card and should decide; the
value must be stated with its reason either way.

## 4. What this lane did not do

No `opencode run`, no shim anywhere, no edit to `packages/**`, `tools/**`, `spec/**`, `corpus/**`,
`research/**`, or `design/TB-PLAN.md`; no re-scoring of the breached run; no ceiling change; no GO for a Hermes
paged arm. The authorization request stands as their card's §9 states it: **one model call, a single-prompt
wired compatibility smoke**, and nothing else spends until it passes.

## 5. Record

This card, one erratum LOG row (four pipes), one day section. My withdrawn `design/TB-WIRED-PLAN.md` is deleted
and was never authoritative. Staged through a private index with explicit paths, then `git read-tree HEAD` on the
shared index; `git-hygiene.sh` OK and `check-handoff.sh` ALL PASS before the commit. Nothing pushed.
