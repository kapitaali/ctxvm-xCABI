# RR-ENGINEPLAN-20261114 — H9: the engine's plan now says why, in one word

The engine rewrote requests and reported only what it cost. Three closed experiment cells were then
diagnosed by arithmetic on `resident` and `headroom` — arithmetic that could not distinguish "the
plan found nothing" from "the keep law owned the request" from "the engine was never asked". This
card adds the plan's own reason to the coverage sidecar, on every selection, without touching the
wire and without breaking the eviction channel's L7 silence.

## 1. What was added

**`packages/hermes/live/context_engine.py`**

- `_plan()` returns its facts as a third value. `reason` is one of a closed set:
  `fits` (everything the plan could keep fits; pinned pages may still reposition),
  `floor_bust` (the keep law's floor alone reaches vBudget, so nothing could be evicted),
  `evicted` (the budget bit and at least one page left the request). Facts also carry
  `floorTokens`, `residentTokens`, `droppedCount`, `droppedTokens`, `repositionedCount`.
- `OBSERVER` gains a second slot, `plan`. `set_observer(cb, plan_callback=None)` keeps the old
  one-argument call working, so an older caller is not broken.
- `select_context()` reports the plan on **every** selection, before the no-change early return.
  The eviction channel (`cb`) is untouched: it still fires only when the request changed, because
  `test_no_report_when_nothing_changes` pins that (L7).
- `prefixHash`: a fixed probe of the request's leading protected block (`sha256:` + 16 hex), capped
  at 8 messages and stopping at the first message this plan changed. It answers "did the head of the
  request change between calls" — H11's question — and is **not** the provider's cache key. Named so
  in the code, because a hash with an unstated basis becomes a second truth later.

**`packages/hermes/live/__init__.py`** — `_record_plan` stamps `plan_by_session[session]` (the last
plan) and `plan_tally_by_session[session][reason]`, per session like every other arm field; the
sidecar's `plugin` block carries `enginePlan` and `enginePlanTally`. Both are `null` for a session
with no plan rather than borrowed from another session in the same process.

**`tools/coverage_check.py`** — presence-gated typing: absent keys pass (every capture written before
today), a present `enginePlan` must be an object, its `reason` must be one of the three names, its
counters must be non-negative integers and its `prefixHash` must be a `sha256:` string.

## 2. Deviations from the card's sketch

| Sketch (H9) | Shipped | Why |
|---|---|---|
| `droppedPages` | **`droppedCount`** (integer) | "pages" reads as a list; the identities already live in `evictedPages` / `callSizes[].removed`. Two meanings of one word is how a field stops being auditable. |
| — | `residentTokens`, `budgetTokens`, `repositionedCount`, `callIndex` added | The reason alone cannot be checked without the two numbers it compares; `callIndex` joins the block to `callSizes[i]`. |
| only `_plan` driven by the test | `_plan` drives the three reasons **and** the sidecar field is asserted | The card's done-when asks for both; the second half is a separate test that goes through `_coverage_manifest` with two sessions in one process. |

## 3. Verification

Unit and sidecar tests, `python3 -m pytest packages/hermes -q` → **207 passed, 15 subtests passed**
(was 201 before this card; +5 engine laws, +1 sidecar attribution).

**Red-before probes** — each mutation was applied, the suite run, and the file restored
byte-identical (`sha256sum` compared before and after):

| Probe | Mutation | Result |
|---|---|---|
| P1 | `"reason": "evicted" if dropped else "fits"` → `"fits"` | `test_evicted_names_the_drop_and_its_tokens` **red** |
| P2 | plan channel call disabled (`None and OBSERVER["plan"](…)`) | **all five** `EnginePlanRecordTests` **red** |
| P3a | a real pre-change capture, unmodified | `coverage_check: consistent … digest ok`, exit **0** — no retro-fail |
| P3b | same capture with a well-formed `enginePlan` injected | exit **0** |
| P3c | `enginePlan.reason = "probably-fine"` | exit **1**, `plugin.enginePlan.reason must be one of fits, floor_bust, evicted` |

**Deployed artifact** — the installed copy was synced with `tools/sync-plugin.sh` (3 files copied,
`0.13.24` on both sides, load check `0.13.24`), then imported by path with only it on `sys.path`:
`_coverage_manifest` from the *installed* file emits `enginePlan` with `reason: evicted` and a
`sha256:` prefix probe, `enginePlanTally {fits: 1, floor_bust: 0, evicted: 2}`, and `null` for a
session that never planned.

**Gate** — `bash tools/run-ci.sh` unpiped, `CTXVM_*` cleared by enumeration → `ts suites green
(24 + 62 + 46 tests); python suites green (207 + 8 + 66 tests)`; `SCHEMA CONFORMANCE: PASS (682
checks)`; `ALL GATES GREEN`. **Wire untouched:** `git status --short | grep -E '^( M|\?\?) (spec|rust|corpus)/'`
returns nothing, so no schema, codec, vector or corpus byte moved and `ts` order is not in play.

## 4. What this does not prove, and what is still owed

- **No live capture carries the block yet.** The gateway (pid 3833, started 09:22:28) predates the
  09:31:36 sync, so it holds 0.13.23. `tools/sync-plugin.sh` reports `GATEWAY STALE` and names the
  restart. The deployed-artifact probe above is the strongest evidence available without it; a real
  session after the restart is the tie-breaker, and the first sidecar it writes should read
  `enginePlan.reason` on a normal interactive turn — most likely `floor_bust` at the 200000 default.
- **`prefixHash` is a probe, not a cache key.** It is comparable between calls of the same arm; it is
  not the provider's prefix and must not be quoted as one.
- **H10 stays open.** It asks for the measured floor of the T-A session in
  `reports/RR-NOOP-20261109.md`; that needs that session's bytes, not this card's.
- **A reviewer ask in `reports/RR-DAY-20261114.md` is still open and is one line in this lane:**
  the plugin block has no `plugin.evictedTokens`, so `coverage_check`'s per-page rule (its
  precondition is `evictedTokens > 0`) stays dormant in production. Not done here — it changes what
  every sidecar attests and wants its own card with a live capture to prove the rule fires.
