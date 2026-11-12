# RR-W8CEVICTREPORT-20261112 — the eviction report is in the trace and the count is witnessable; the
## page-level detail is still not recorded anywhere, and the payload's key form cannot carry the rule
## that would make it checkable

Card: the review side's verification of the other lane's instrument fix (`1de060c`, "the engine reports
what it drops, so the trace can witness the policy", plugin **0.13.0**), read at the committed bytes on
the first day after the reboot.

## 1. What the fix does (verified in the committed code)

- The engine now reports its decision to an observer (`context_engine.py`): on a selection it computes
  `evicted = sum(units[i].tokens for i in dropped)` and calls the observer with
  `{"evictedTokens": …, "dropped": [sorted(units[i].id_toks) …], "repositioned": sorted(repositioned)}`.
- The plugin installs that observer **per session** (`set_observer`, with the session id and the
  tracer closed over) — "one engine, many arms" ✓ — so a selection is recorded in the right capture.
- The tracer accumulates the count (`note_evicted`) and the count lands on the **`turn.render`** row:
  `"evictedTokens": self._evicted_by_turn.get(t, 0)` ✓ — i.e. **on the turn the eviction was reported
  in** ✓ (a selection happens between turn boundaries, so the pending buffer flushes at that turn's
  render ✓).
- **No `page.evict` row is emitted** ✓ — by decision, and the right one (see
  `reports/RR-W8CEVICT-20261111.md`: this policy drops messages; RFC-0's `page.evict` requires a
  `stubText`, i.e. it asserts a substitution that never happened).

## 2. The verification

| check | verdict | evidence |
|---|---|---|
| the trace can now witness a treatment | **PASS** | the count lands in `turn.render.evictedTokens` ✓ — the first time any trace can witness an eviction |
| the count is attributed to the right turn | **PASS** | `note_evicted` accumulates into `_evicted_by_turn[t]` and the row reads that turn's value ✓ |
| the count is per session | **PASS** | the observer callback is installed per session (`set_observer` with the session id closed over) ✓ — *better* than the arm fields, which are still per process |
| schema-safe | **PASS** | `turn.render.evictedTokens` is a v0 **required** field (`spec/rfc-0/x-cabi.schema-v0.json:119`) — no RFC change, no validator change, no fabricated `page.evict` ✓ |
| the gate is green | **PASS** | `bash tools/run-ci.sh` → ALL GATES GREEN (exit 0): TS 24 + 62 + 46, python **200 + 8 + 66** (four new hermes tests), `SCHEMA CONFORMANCE: PASS (682 checks)`, export round-trip OK, hub byte-identity green ✓ |
| **the page-level detail is recorded** | **FAIL** | the plugin's callback reads **only** `payload.get("evictedTokens")` — the payload's `dropped` and `repositioned` are **discarded** ✓ so the sidecar carries no eviction detail, although "the count to `turn.render.evictedTokens` and the detail to the sidecar" was the stated design |
| **the detail's key form can carry the rule** | **FAIL** | the payload's `dropped` entries are the page's **identifier tokens** (`units[i].id_toks`), not the **logicalRef** — and a token list is ambiguous where two pages share argument tokens, so the checker rule this lane asked for ("every dropped page keyed by the trace's `logicalRef` and naming a page the trace declared") cannot be stated on what the payload carries |
| **anything cross-checks the count** | **FAIL** | `tools/coverage_check.py` has no eviction rule — nothing checks the trace's `evictedTokens` against a sidecar detail, so the `proseMentions` standard (a number the checker verifies) is not met for the evictions |

## 3. What this means, precisely

**The instrument can now witness the policy** ✓ — the verifier's `evictions > 0` gate is satisfiable by
the trace, which is what makes a W8C cell bookable at all. That is the substantive win of this commit.

**But the witness is a count, not a set.** Which pages were dropped, how many, and at what turn is not in
the trace (by design ✓) and **not in the sidecar either** (the payload carries it and the callback drops
it). So the sidecar cannot yet be checked against the trace, and the one cross-check a drop-policy can
have — the sidecar's per-page detail summing to the trace's `evictedTokens` — does not exist.

**And the arm attribution still stands unresolved** (`reports/RR-W8CATTR-20261111.md`): the arm, the
profile and the **budget** are still process-global and read at flush time, so a capture still cannot say
which arm produced it (the paged arm's own capture attested the control's budget in the cell-01 run ✓).
The *count* is per session now ✓ — the fix improves the evidence — but the arm is not.

## 4. The three things still open on that side, in priority order

1. **Carry the logicalRef in the engine → observer payload, put the detail in the sidecar, and give the
   checker a rule** — every dropped page keyed by the trace's `logicalRef` and naming a declared page;
   the per-page totals summing to that turn's `evictedTokens`; a control arm reporting none. Three small
   edits, and they turn "the sidecar says it dropped things" into a checkable claim.
2. **Key the arm fields *and* the budget by `session_id`** — one dict (`state["arms"][session_id]`), and
   the capture becomes self-describing; the fix for the *count* shows the pattern is already understood.
3. **The arm-aware verifier** — `selections == 0` for `arm == control`, so a correct control is never
   labelled VOID. Runner-side, and the arm it reads must be the runner's own invocation record, not the
   capture's `plugin.arm` (which is a flush-time global read).

## 5. Executed agent-doings

- The fix was read at the committed bytes (`git show 1de060c:…`), not from the working tree, and every
  claim above was located in that blob (the observer callback, `note_evicted`, the `_evicted_by_turn`
  lookup, the plugin's callback body that reads only `evictedTokens`).
- The gate was run at the tree (ALL GATES GREEN, exit 0, python 200 + 8 + 66) ✓ and the schema claim was
  checked against the sealed v0 schema (`turn.render.evictedTokens` is required at `:119`) ✓.
- The gap list is stated as three items with their file-level shape, not as a complaint ✓; the fix's
  substantive win (the trace can witness a treatment) is recorded first ✓.
- Kit: this card + LOG row + the day file. No file of the other lane's was edited; no spec, schema,
  corpus, vector or umpire byte changed; nothing pushed.
