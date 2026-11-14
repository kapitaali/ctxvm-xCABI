# RR-H9LANDING-20261114 — review of the hermes lane's H9 landing (`e480186`, plugin 0.13.24): **seven measured defects**, **four** of them one-line fixes, and the ruled per-call rule still has no live witness

Card: review-lane verification of the other lane's H9 landing (`e480186` ✓, `reports/RR-ENGINEPLAN-20261114.md` ✓,
plugin **0.13.24** ✓) against the review-side input card (`reports/RR-H9-INPUT-20261113.md` ✓) and the P12 ruling
(`reports/RR-OMISSIONANSWER-20261113.md` ✓). **Verification only** ✓ — no `packages/**` ✓, no `tools/**` ✓, no `design/**` ✓
edited here ✓; the asks in §8 are proposals for the hermes lane ✓.

---

## 0. Verdict in one table

| the landing's claim ✓ | measured ✓ | verdict ✓ |
|---|---|---|
| the reason fires on **every** selection ✓ | 205 selections ⇒ 205 plan payloads ✓; the eviction channel stayed silent on a no-op ✓ (L7 intact ✓) | **LANDED** ✓ |
| `reason ∈ {fits, floor_bust, evicted}` ✓ | three names, but `fits` also names a **rewritten** request ✓ (§1 ✓) | **PARTIAL** ✓ |
| `floorTokens` per call ✓ | per call in the payload ✓, **not** per call in the sidecar ✓ (§3 ✓) | **PARTIAL** ✓ |
| `prefixHash` answers "did the head change between calls" ✓ | the hash's **input length moves with the cut** ✓ ⇒ two calls with identical heads hash differently ✓ (§2 ✓) | **FALSE as stated** ✓ |
| the checker types the block ✓ | it types the **words** ✓ and never checks them against the numbers beside them ✓ (§4 ✓) | **PARTIAL** ✓ |
| the wire and `ts` untouched ✓ | no `spec/`, `rust/` or `corpus/` path in the diff ✓ | **HELD** ✓ |
| the installed copy is in sync ✓ | 4 files byte-identical ✓ (`sync-plugin.sh --check` ✓: `PLUGIN_VERSION: repo 0.13.24 \| installed 0.13.24 \| manifest 0.13.24` ✓) | **HELD** ✓ |
| the gateway holds the build ✓ | pid **23669** started after the 09:31:36 sync ✓ ⇒ it holds **0.13.24** ✓ | **CLOSED** ✓ (the RR-VERSIONDRIFT ask is moot ✓) |

⇒ ⇒ **the landing is real and the reason field works** ✓ ⇒ ⇒ **seven** defects ✓ (the probe's byte form ✓ is part of
defect 2 ✓ — the same field ✓) ⇒ ⇒ all in the block's own semantics or its check ✓ ⇒ ⇒ **none of them needs a schema change** ✓ ⇒ ⇒ **four** are **one-line** fixes ✓ (A1 ✓, A4 ✓, A5 ✓, A8 ✓) ⇒ ⇒ and the ruled
per-call rule still has **no live witness** ✓ (§6 ✓).

---

## 1. `fits` also names a request the engine **rewrote** ✓ — the enum is still incomplete ✓

The reason is computed from the drop set alone ✓ (`packages/hermes/live/context_engine.py:818` ✓:
`"reason": "evicted" if dropped else "fits"` ✓) ⇒ ⇒ a selection that **repositions pinned pages without dropping
anything** reports `fits` ✓ ⇒ ⇒ although the request **was rewritten** ✓.

Measured, driving the engine directly ✓ (the plugin's own test harness ✓, `packages/hermes/test/test_context_engine.py` ✓):

```python
import sys; sys.path.insert(0, "packages/hermes/test")
import test_context_engine as T
ce, _msg, _call, _result = T.ce, T._msg, T._call, T._result
base = [_msg("system","s"), _msg("user","u"),
        _msg("assistant","", tool_calls=[_call("c1","notes/f01.md")]),
        _msg("tool", _result(6_000,"f01"), tool_call_id="c1"),
        _msg("assistant","", tool_calls=[_call("c2","notes/f02.md")]),
        _msg("tool", _result(6_000,"f02"), tool_call_id="c2")]
eng = ce.build_engine(); ev, pl = [], []
eng.set_observer(ev.append, pl.append)
eng.select_context(list(base))            # first call: nothing pinned yet
T._pin_via_refault(eng, "notes/f02.md")   # the model re-asks for f02 ⇒ a pin
out = eng.select_context(list(base))      # the pin repositions the block
print(pl[-1]["reason"], pl[-1]["repositionedCount"], len(ev), out is not None)
```

⇒ `fits 1 1 True` ✓ ⇒ ⇒ **the reason says `fits` for a request the engine rewrote** ✓ ⇒ ⇒ the eviction channel
**did** fire ✓ (`len(ev) == 1` ✓) ⇒ ⇒ and `out is not None` ⇒ ⇒ the request changed ✓.

Scale, from the engine's own shared log ✓ (`~/.local/state/ctxvm/traces/_decision.log` ✓, all rows with both
counters ✓): **554** decisions are *reposition-only* ✓ (dropped 0, repositioned > 0 ✓) ⇒ ⇒ all of them would be
`fits` ✓ ⇒ ⇒ against **858** that dropped something ✓ ⇒ ⇒ and **1,899** that changed nothing ✓ ⇒ ⇒ so `fits`
would name **2,453** decisions of which **554** are changed requests ✓.

⇒ **Honesty about the traffic** ✓: those 554 are the **test-suite** homes ✓ (`'/suite'` ✓, `'/y'` ✓); the **363**
real-home decisions ✓ (`/home/theb/.hermes**` ✓) contain **139** drops ✓ and **0** reposition-only ✓ ⇒ ⇒ **the case
is a live code path, not yet observed in real traffic** ✓ ⇒ ⇒ it will fire the moment a pinned page is re-read
under pressure ✓.

⇒ ⇒ the review-side input card's §3 ask ✓ (`reports/RR-H9-INPUT-20261113.md` §3 ✓: *"the enum is incomplete —
the engine has a fourth outcome"*) is **confirmed against the shipped code** ✓ ✓.

---

## 2. `prefixHash`'s **input length moves with the cut** ⇒ ⇒ the hash cannot answer its stated question ✓

The probe is `request_messages[: min(_cut, 8)]` ✓ (`context_engine.py:492` ✓) where `_cut` is the index of the
**first message this plan changed** ✓ (`context_engine.py:488` ✓) ⇒ ⇒ so the hashed window is **8 messages for a
no-op** ✓ and **shorter for a plan that changed something early** ✓ ⇒ ⇒ two calls whose head is **byte-identical**
hash **differently** ✓ ⇒ ⇒ "did the head change between calls?" is **not** answerable by comparing the hashes ✓.

Measured ✓ (same transcript, one engine at a budget that fits ✓, one at a budget that bites ✓):

```
fits   : sha256:e3bb38d85c25de9b   == hash(head[:8])   -> True
evicted: sha256:662bcfbb90f95f9a   == hash(head[:5])   -> True
the two differ although head[:8] is byte-identical: True
```

⇒ ⇒ the card's sentence ✓ (*"It answers 'did the head of the request change between calls' — H11's question"*)
is **false for the cross-plan case** ✓ ⇒ ⇒ the card's own basis sentence ✓ (*"capped at 8 messages and stopping
at the first message this plan changed"*) is **accurate** ✓ ⇒ ⇒ the defect is that the two sentences disagree ✓
⇒ ⇒ a reader who compares two `prefixHash` values cannot tell *head changed* from *cut moved* ✓.

⇒ ⇒ **the fix is one line** ✓: hash a **fixed** window ✓ — and hash it in the **C3 byte form** ✓
(§7(d) ✓: the probe's byte form diverges from the conformance vector in **every** case ✓) ⇒ ⇒ both halves are
one line each ✓ (`request_messages[:8]` ✓, or a window that stops at a
**fixed** message count ✓) ⇒ ⇒ the hash then means what the card says it means ✓ ⇒ ⇒ and it stays comparable
across arms ✓ ✓.

⇒ ⇒ note this is the **second** time the adapter chose a hash basis without the owner's ruling ✓ — the P11 ruling
✓ (`handoff/QUESTIONS.md` ✓: *"(c) owner, (a) pointer; test FIRST (equal model/page table/report, never bytes)"* ✓)
says the **canonical form is the owner's** ✓ ⇒ ⇒ the H9 input card's §5 ask ✓ was **not met** ✓ ⇒ ⇒ and the
cost is now measured ✓: the field cannot answer the question it was shipped to answer ✓ ✓.

---

## 3. The floor **series** and the **turn** are not retained ⇒ ⇒ H10 still has no bytes ✓

The sidecar keeps the **last** plan per session ✓ (`packages/hermes/live/__init__.py:1529` ✓:
`_st.setdefault("plan_by_session", {})[_target] = dict(payload or {})` ✓ — overwritten each selection ✓) and a
**tally of reason counts** ✓ (`:1530-1535` ✓) ⇒ ⇒ the per-call `floorTokens` ✓ is computed ✓ and then **dropped** ✓
⇒ ⇒ the plan block carries **no turn** ✓ (`reason`, `floorTokens`, `residentTokens`, `droppedCount`,
`droppedTokens`, `repositionedCount`, `budgetTokens`, `prefixHash`, `callIndex` ✓ — measured ✓ — **no `turn`** ✓).

Measured ✓ (10 selections ✓, one engine ✓): the reason tally is `{fits: 10}` ✓ ⇒ ⇒ the sidecar would carry **one**
plan ✓ (the last ✓) ⇒ ⇒ and **no floor series** ✓ ⇒ ⇒ H10's done-when ✓ (*"the report contains `floorTokens` and
the turn spread that produced it"*, `design/ROADMAP-HERMES-LANE.md:89-91` ✓) is **still not answerable from a
capture** ✓ ⇒ ⇒ the other lane's own card says so ✓ (*"H10 still needs the T-A bytes"*, `e480186` ✓) ✓.

⇒ ⇒ the fix is small and in the same shape as `callSizes` ✓ ⇒ ⇒ keep a **per-call plan list** ✓ (reason, floor,
turn, callIndex ✓) beside the tally ✓ ⇒ ⇒ then H10 is a **read** ✓ ⇒ ⇒ and the review-side input card's §4 ask ✓
(*"the floor is per call … and carry the turn"*) becomes met ✓ ✓.

---

## 4. The checker types the plan's **words** ✓ and never checks them against the numbers beside them ✓

`tools/coverage_check.py` ✓: the block is typed **when present** ✓ (`:390-408` ✓), the reason must be one of the
three names ✓ (`:400` ✓), the counters must be integers ✓ (`:401-405` ✓, via `_int` ✓ at `:95-96` ✓), the
`prefixHash` must be a `sha256:` string ✓ (`:406-408` ✓) ⇒ ⇒ **nothing cross-checks the reason against the block's
own numbers** ✓ ⇒ ⇒ and `_int` accepts **negative** integers ✓ ⇒ ⇒ **five** synthetic plans, all **accepted** ✓
(real 0.13.21 capture ✓ as the base ✓, `traceDigest` recomputed ✓, `traceFile` matched ✓):

| variant ✓ | what it claims ✓ | checker says ✓ |
|---|---|---|
| `evicted` with `droppedCount: 0, droppedTokens: 0` ✓ | a drop that dropped nothing ✓ | **consistent** ✓ |
| `floor_bust` with `floorTokens: 10` against `budgetTokens: 200000` ✓ | a floor bust that is not ✓ | **consistent** ✓ |
| `fits` with `droppedTokens: 90000` ✓ | a fit that dropped 90k ✓ | **consistent** ✓ |
| `reason` only, no counters ✓ | a decision with no numbers ✓ | **consistent** ✓ |
| `floorTokens: -5, droppedCount: -3, …` ✓ | negative counters ✓ | **consistent** ✓ — while the message says *"must be a non-negative integer"* ✓ (`:404` ✓) |

⇒ ⇒ the "closed set a verifier can branch on" ✓ is a closed set of **words** ✓ ⇒ ⇒ a verifier that branches on it
gets **no** guarantee that the word matches the numbers ✓ ⇒ ⇒ the three cross-checks are **one line each** ✓:

- `evicted` ⇒ `droppedCount > 0` and `droppedTokens > 0` ✓
- `floor_bust` ⇒ `floorTokens >= budgetTokens` ✓ (the engine's own test asserts exactly this ✓, `test_context_engine.py` ✓)
- `fits` ⇒ `droppedCount == 0` ✓

⇒ ⇒ and `_int` must reject negatives ✓ ⇒ ⇒ `value >= 0` ✓ ⇒ ⇒ **the message and the check must agree** ✓.

⇒ ⇒ **the plan block's presence is not required at 0.13.24** ✓ (measured ✓): a capture with
`plugin.version = "0.13.24"` ✓, `engineSelections: 16` ✓ and **no** `enginePlan` ✓ passes ✓ ⇒ ⇒ a broken emitter
(the plan channel never firing ✓) is **invisible to the checker** ✓ ⇒ ⇒ the per-call rule is version-gated ✓
(`:367` ✓) but the plan rule is **not** ✓ ⇒ ⇒ version-gate it the same way ✓.

---

## 5. The per-call **tolerance clause** is keyed on the *settings* budget ⇒ ⇒ the consistency direction is dormant in the default shape ✓

The clause fires only when `before > budget` ✓ (`tools/coverage_check.py:382` ✓) where `budget` is
`plugin.budgetTokens` ✓ (`:366` ✓) — the **settings** number ✓ (default **200,000** ✓,
`packages/hermes/live/__init__.py:830` ✓) — while the engine's **operative** budget is the plan's `budgetTokens` ✓
(`context_engine.py:497` ✓; measured **24,000** in the suite ✓) ⇒ ⇒ when the settings number exceeds the request
size the clause is **skipped entirely** ✓ ⇒ ⇒ the "named tokens must account for the size change" direction ✓
(the P12 ruling's second clause ✓) **never runs** ✓.

Measured ✓ (real capture as the base ✓; one call that names **half** its drop ✓, and one that names **zero** ✓):

```
plugin.budgetTokens = 200000, plan.budgetTokens = 24000, names 14500 of a 29000 drop  -> consistent (exit 0)
plugin.budgetTokens =  24000, the same capture                                        -> VIOLATION (tolerance 10 %)
plugin.budgetTokens = 200000, names 0 of a 29000 drop                                  -> consistent (exit 0)
```

⇒ ⇒ the plan block **already carries the engine's budget** ✓ ⇒ ⇒ the checker has the right number in hand and does
not use it ✓ ⇒ ⇒ **one line**: key the clause on the plan's `budgetTokens` ✓ (or on the smaller of the two ✓) ✓ ⇒ ⇒
and the consistency direction comes back to life ✓ ✓.

⇒ ⇒ this is the **same dormancy** the review-side checker-gaps card found ✓ (`reports/RR-CHECKER-GAPS-20261114.md` ✓:
the fail-closed half unenforced ✓) ⇒ ⇒ **both halves of the ruled rule are still unenforced in the default shape** ✓
⇒ ⇒ the two asks of that card remain **open** ✓ ✓.

---

## 6. The live witness: the first 0.13.24 capture exists ✓ and it is a **control** arm ✓ ⇒ ⇒ the ruled rule still waits ✓

- The gateway **pid 23669** ✓ started **after** the 09:31:36 sync ✓ ⇒ ⇒ it holds **0.13.24** ✓
  (`bash tools/sync-plugin.sh --check` ✓: *"gateway: pid 23669 started after these files were written; it holds
  this build"* ✓) ⇒ ⇒ **the RR-VERSIONDRIFT ask is moot** ✓ ⇒ ⇒ the version is no longer a blocker ✓.
- The newest live capture ✓ (`local-35a51dd9…` ✓, mtime **09:59:22** ✓) is **v=0.13.24** ✓, `arm: control` ✓,
  `engine: null` ✓, `engineSelections: 0` ✓, `enginePlan: null` ✓ ⇒ ⇒ the control arm returns before `_plan` ✓
  (`context_engine.py:447` ✓, `RETURNED-CONTROL` ✓) ⇒ ⇒ so **no plan block** ✓ and **no per-call list** ✓ ⇒ ⇒
  the ruled per-call rule still has **no live witness** ✓ ⇒ ⇒ what is owed is a **paged** capture on 0.13.24 ✓ ✓.
- The installed copy is **byte-identical** to the repo ✓ — `live/__init__.py` ✓, `live/context_engine.py` ✓,
  `src/plugin.py` ✓, `live/plugin.yaml` ✓ (sha256 compared file by file ✓) ✓ ⇒ ⇒ the sync is **verifiable** ✓, not
  asserted ✓ ✓.

---

## 7. Three smaller measurements ✓ (the first is defect 2's second half ✓)

**(a) `residentTokens` now means two things inside one sidecar file** ✓ ⇒ the plan's value is **request** residency ✓
(`context_engine.py:786` ✓: `sum(_tokens_for(m) for m in messages)` ✓) ⇒ ⇒ the wire's and `perCall[]`'s value is
**table** residency ✓ (`packages/hermes/src/plugin.py:563` ✓, `ctxvm-core tally_at` ✓) ⇒ ⇒ the README limitation row
✓ (*"`residentTokens` is table residency, not request residency"* ✓) covers the wire field ✓ ⇒ ⇒ **not** the plan
block's ✓ ⇒ ⇒ a reader joining `plugin.enginePlan.residentTokens` to `perCall[].residentTokens` compares two
different quantities ✓ ⇒ ⇒ **rename** the plan's field ✓ (e.g. `requestTokens` ✓) or say so beside it ✓ ✓.

**(b) The plan's `callIndex` and the sidecar's per-call `i` are different numbers for the same call** ✓ ⇒ and both
**saturate** ✓. The plan reports `len(CALL_LOG)` ✓ (`context_engine.py:499` ✓) *before* the append ✓; the eviction
payload reports `len(CALL_LOG) - 1` ✓ (`:586` ✓) *after* it ✓; `CALL_LOG` is trimmed to **200** entries ✓
(`:539` ✓) and is a **process global** ✓ (`:270` ✓, never cleared ✓) ⇒ ⇒ after 200 calls the plan says **200** ✓ and
the sidecar's per-call `i` says **199** ✓ ⇒ ⇒ and both repeat forever ✓ ⇒ ⇒ measured: the plan's tail is
`[200, 200, 200, 200, 200]` ✓ and the eviction channel's is `[199, 199, 199, 199, 199]` ✓ ⇒ ⇒ the sidecar's per-call
`i` is **not a per-session sequence** ✓ (it is a process-wide counter ✓) ⇒ ⇒ and **not unique** ✓ ⇒ ⇒ so a
per-call record keyed on it cannot be addressed ✓ ⇒ ⇒ **one ask**: make the plan's index the **same** integer the
per-call list uses ✓ and state the cap ✓ ✓.

**(c) The plan channel inherits the single global observer slot** ✓ ⇒ ⇒ two sessions interleave ⇒ ⇒ A's selection
can be recorded into B's bucket ✓ (measured ✓: `A: 0, B: 1` ✓) ⇒ ⇒ the same hazard the eviction channel has ✓
(pre-existing ✓) ⇒ ⇒ but H9 adds a **per-session** field on top of it ✓ ⇒ ⇒ the mixup becomes **observable in a
named field** ✓ ⇒ ⇒ worth one line in the hermes lane's card ✓, not a blocker ✓ ✓.

**(d) The probe's **byte form** is not the repo's **C3** form** ✓ ⇒ ⇒ a digest that cannot be compared across
implementations ✓. The probe hashes `json.dumps(_probe, sort_keys=True, default=str)` ✓
(`context_engine.py:492-497` ✓) ⇒ ⇒ measured against the **conformance vector** ✓
(`rust/crates/ctxvm-conformance/vectors/canonical-form-cases.jsonl` ✓ — the executable form of C3 ✓):

```
the C3 form  (ensure_ascii=False, minimal separators) vs the vector: 8 match, 0 mismatch
the H9 form  (json.dumps defaults)                   vs the vector: 0 match, 8 mismatch
```

⇒ ⇒ **C3 is the repo's normative canonical form for a hash input** ✓ (D18 ✓, applied 2026-11-11 ✓:
*"the canonical form of a hash input is specified by the conformance test … and is normative for every
implementation"* ✓) ⇒ ⇒ and the TS mirror already implements it ✓ (`packages/node/src/ident.ts:35` ✓,
`canonicalJson` ✓ — 24/24 node tests green in a clean env ✓) ⇒ ⇒ so the H9 probe **diverges from the vector in
every canonical case** ✓ ⇒ ⇒ three measured differences ✓: whitespace separators ✓, ASCII-escaped non-ASCII ✓,
and `default=str` ✓ (which **coerces** anything non-JSON ✓ — the very thing C3 forbids ✓: *"An inadmissible
input MUST be rejected, never coerced"* ✓) ⇒ ⇒ and `default=str` on a `set` is **PYTHONHASHSEED-dependent** ✓
(measured ✓: three seeds ⇒ three byte strings ✓ ⇒ ⇒ **not reproducible** ✓ ✓).

⇒ ⇒ **scope, honestly** ✓: the probe is a **sidecar** field ✓, not a wire field ✓ ⇒ ⇒ C3's letter binds hash
inputs **in the RFC-0.1 note** ✓ ⇒ ⇒ so this is **not** a violation of a sealed spec ✓ ⇒ ⇒ it is a **latent**
divergence ✓ ⇒ ⇒ harmless while only the Python plugin writes it ✓ ⇒ ⇒ and **wrong** the moment anyone compares
the digest across implementations ✓ (the TS mirror ✓ is a **third** form ✓ ⇒ ⇒ **one line**: hash the C3 byte
form ✓ (`ensure_ascii=False` ✓ + minimal separators ✓) ✓ ✓.

⇒ ⇒ **and a note for the owner** ✓: the hermes plugin's own `canonical_json` ✓
(`packages/hermes/src/plugin.py:35` ✓) matches the vector in **3** of 8 cases ✓ (it ASCII-escapes ✓) ⇒ ⇒ it
serves the **RFC-0 §6** reference digest ✓ (sealed ✓, unchanged ✓) ⇒ ⇒ **not** a violation ✓ ⇒ ⇒ but it is
**not** the C3 form ✓ ⇒ ⇒ so "use the plugin's own helper" would be the **wrong** pointer ✓ ⇒ ⇒ the pointer is
the **vector** ✓ ✓.
**(e) The hermes suite is environment-sensitive** ✓ ⇒ ⇒ the landing's *"207 passed"* ✓ reproduces only in a clean
environment ✓ ⇒ ⇒ with the gateway's ambient `CTXVM_*` variables exported ✓, **11** tests fail ✓ (measured ✓:
`CTXVM_TRACE_TS=0` alone ⇒ 9 failures ✓; `CTXVM_BUDGET_TOKENS` ⇒ 1 ✓; `CTXVM_HERMES_VERSION` ⇒ 1 ✓) ⇒ ⇒ with
`env -i` ⇒ **207 passed, 15 subtests** ✓ ⇒ ⇒ a re-runner should know that before calling the suite red ✓ ⇒ ⇒
**not** a defect in the landing ✓ ⇒ ⇒ recorded so the next reviewer does not misread it ✓ ✓.

---

## 8. The asks (proposals for the hermes lane — **nothing filed here** ✓)

| # ✓ | ask ✓ | where ✓ | size ✓ |
|---|---|---|---|
| A1 ✓ | give the rewrite a name of its own ✓ (a fourth reason ✓, or rename `fits` to say "nothing dropped" ✓) | `context_engine.py:818` ✓ | 1 line ✓ |
| A2 ✓ | hash a **fixed** window ✓, in the **C3 byte form** ✓ (`ensure_ascii=False` ✓ + minimal separators ✓,
the vector ✓), so `prefixHash` answers the question it claims ✓ and one input ⇒ one digest ✓ | `context_engine.py:488-497` ✓ | 2 lines ✓ |
| A3 ✓ | cross-check the reason against the counters ✓ (three one-liners ✓) and reject negative counters ✓ | `tools/coverage_check.py:401-405` ✓ | 4 lines ✓ |
| A4 ✓ | version-gate the plan block's **presence** ✓, the way the per-call rule is gated ✓ | `tools/coverage_check.py:390` ✓ | 1 line ✓ |
| A5 ✓ | key the tolerance clause on the **engine's** budget ✓ (the plan block carries it ✓) | `tools/coverage_check.py:366,382` ✓ | 1 line ✓ |
| A6 ✓ | keep a **per-call plan list** ✓ (reason, floor, turn, index ✓) beside the tally ✓ ⇒ ⇒ H10 becomes a read ✓ | `live/__init__.py:1529` ✓ | ~10 lines ✓ |
| A7 ✓ | make the plan's index the **same** integer the per-call list uses ✓, and say the cap ✓ | `context_engine.py:499` ✓, `live/__init__.py:1506` ✓ | 2 lines ✓ |
| A8 ✓ | rename the plan's `residentTokens` ✓ (or state the two meanings beside it ✓) | `context_engine.py:786` ✓ | 1 line ✓ |

⇒ ⇒ **sizes** ✓: **four** asks are **one line** each ✓ (A1 ✓, A4 ✓, A5 ✓, A8 ✓), **three** are 2–4 lines ✓
(A2 ✓, A3 ✓, A7 ✓), and **one** is ~10 lines ✓ (A6 ✓) ⇒ ⇒ the LOG row's split of that count ✓ is off by two ✓ ⇒ ⇒ an
**erratum row** ✓ follows it ✓ ✓.

⇒ ⇒ **the owner's side** ✓: **two** different questions ✓ ⇒ ⇒ (i) the **byte form of a hash input** ✓ is **settled** ✓ —
C3 ✓, and the probe must use it ✓ (A2 ✓) ⇒ ⇒ (ii) the **probe's own canonicalisation** ✓ — *what* is hashed ✓, in
*which order* ✓, over *which window* ✓ — is still the **owner's** ✓ (P11 ✓) ⇒ ⇒ A2's window is the lane's *interim*
choice ✓ ⇒ ⇒ and the P11 pointer should be settled before the field reaches a **published** capture ✓ ⇒ ⇒ **one open
decision, already routed** ✓ ✓.

---

## 9. Executed agent-doings

- The landing read ✓ (`e480186` ✓) ⇒ the diff's paths checked ✓ (**no** `spec/`, `rust/`, `corpus/` ✓) ⇒ the engine's
  `_plan` facts read ✓, the plan channel read ✓, the observer guard read ✓, `CALL_LOG`'s trim read ✓, the sidecar's
  writers read ✓, the checker's plan rule read ✓ ✓.
- The engine driven **directly** ✓ (the plugin's own harness ✓): the reason on every selection ✓ (205 ⇒ 205 ✓), the
  reposition-only case ✓ (`fits 1 1 True` ✓), the `prefixHash` basis ✓ (two hashes, one head ✓), the index
  saturation ✓ (plan 200 vs eviction 199 ✓), the single-slot attribution ✓ (`A: 0, B: 1` ✓) ✓.
- The shared log parsed ✓: 3,311 decisions ✓ ⇒ 858 dropped ✓ / 554 reposition-only ✓ / 1,899 no-change ✓ ⇒ and the
  **363** real-home decisions ✓ ⇒ 139 drops ✓ and **0** reposition-only ✓ ⇒ ⇒ the real-traffic caveat stated ✓ ✓.
- **ten** synthetic sidecars ✓ for this card's findings ✓ (derived from the real 0.13.21 capture ✓, digest
  recomputed ✓, `traceFile` matched ✓) run through `tools/coverage_check.py` ✓ ⇒ the plan-word/plan-number and
  negative-counter results ✓ (§4 ✓), the presence-gate result ✓ (§4 ✓), the budget-keyed tolerance result ✓ (§5 ✓)
  and the fail-closed result ✓ (§5 ✓) ✓.
- The installed copy compared file by file ✓ (**4 files, sha256** ✓) ⇒ `sync-plugin.sh --check` ✓ ⇒ the gateway's
  start time vs the sync time ✓ ⇒ the newest live capture read ✓ ✓.
- The gate run ✓ ⇒ **ALL GATES GREEN** ✓ (rust ✓, ts 24+62+46 ✓, python 207+8+66 ✓, schema **682** checks ✓, hub
  byte-identity ✓) ✓ ⇒ `bash tools/check-handoff.sh` ✓ ⇒ **ALL HANDOFF CHECKS PASS** ✓ ⇒ `bash tools/git-hygiene.sh`
  ✓ ⇒ OK ✓.
- Nothing of another lane edited ✓; nothing pushed ✓ ✓.

**Repro for §1, §2, §3, §6, §7** ✓: the snippets above ✓, run from the repo root ✓, with
`CTXVM_TRACE_DIR` pointed at a scratch directory ✓ ✓.
