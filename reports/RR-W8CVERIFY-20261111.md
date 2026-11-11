# RR-W8CVERIFY-20261111 — the instrument commit verified against the six-item list: five PASS, one GAP
## (the prose-mention count is now invisible in the capture), and this lane's earlier "byte-identical"
## claim corrected

Card: the review side's verification of the other lane's W8C step 1 (`7e0f2df`, "plugin 0.12.0: a fault
means the model asked again, not that prose named the page"), run against the **committed** bytes with
the six-item list written down beforehand (`reports/RR-W8CSTEP1-20261111.md` §2).

## 1. The six items, checked

| # | item | verdict | evidence (committed bytes) |
|---|---|---|---|
| 1 | the text signal is **removed**, not weakened | **PASS** | `_credit_demand` (`packages/hermes/live/context_engine.py:496-525`) now counts prose as telemetry only — `page["prose_mentions"] = page.get("prose_mentions", 0) + 1  # telemetry, never a pin`. No `_ensure_pinned` call remains on the text path; the only two that remain are the re-render path (`:485-487`) and `note_refault` (`:547-548`) |
| 2 | `note_refault(ref)` exists and is fed by `pre_tool_call` | **PASS** | `note_refault(args)` (`:528-550`) tokenises the tool call's argument payload with the **same rule the page table uses** (`_value_tokens`), so the identity cannot drift between observer and engine; it pins at `demand_count >= 2` and returns the number of pages newly pinned. Fed from `packages/hermes/live/__init__.py:1216` (`engine.note_refault(kwargs.get("args"))`) inside the `pre_tool_call` hook |
| 3 | pins/faults by source reported | **PASS in substance** | the sidecar carries `"faultsBySource"` (`live/__init__.py:594-597`, written at `:659`), counted from the fault rows by source. With the observer aligned, that tally **is** the engine's pin signal (`tool_recall` = the model's re-read) — the discriminator the diagnostic needs |
| 4 | the observer is aligned (prose is telemetry, `identifier_scan` emits no fault) | **PASS** | `packages/hermes/src/plugin.py:428` documents that the scan "used to emit `page.fault` with source `identifier_scan`, which made the trace say a page …"; the mention count is kept (`:438`, `page["mentions"]`) |
| 5 | the four tests carry their **before-behaviour** | **PASS** | `test_context_engine.py`: `test_prose_does_not_pin_and_a_refault_does` (the discriminating one), `test_re_sent_result_does_not_pin` (the invariant guard), `test_refault_pins_and_is_counted` (the regression guard for the removal), `test_refault_with_unreadable_args_demands_nothing` (the fail-open edge case) — plus the law suite. Their commit message: "Six tests, one of which failed before the change" |
| 6 | the gate is green with a clean env | **PASS** | `env -u CTXVM_TRACE_TS -u CTXVM_HERMES_VERSION bash tools/run-ci.sh` → **ALL GATES GREEN**, exit 0: `check-node-build: OK — 16 events byte-identical`; TS suites **24 + 62 + 46**; python **196 + 8 + 66** (the hermes suite alone: **196 passed**); `SCHEMA CONFORMANCE: PASS (682 checks)`; export round-trip OK; hub byte-identity green |

**So step 1's own gate — "instrument, gate green" — is met**, and the fixture was regenerated **without
`--force`** and carried in the same commit as the observer change (law 6: emitter-produced fixtures are
regenerated, never hand-edited) ✓.

## 2. The gap: the prose-mention count is now invisible in the capture

`prose_mentions` and `refaults` appear **nowhere** in the sidecar or the observer's output (grep: no
hits outside the engine) — the count lives only in the engine's internal page table. The consequence is
precise and worth fixing **before the diagnostic runs**:

> A capture can no longer distinguish **"the scan still SEES the prose and does not pin"** from **"the
> scan is blind"**. In the trace the two look identical — no `identifier_scan` fault in either case —
> and the second is exactly the **B1-class death** the `identifier_scan` fault used to make visible.

The fixture path is protected by their own in-process guard (the generator asserts `mentions >= 1`), so
the *fixture* cannot go blind silently. But a **live** session's sidecar shows nothing, and the
diagnostic (step 4) is a live run whose job is to show that "nothing pins and growth per turn is
unchanged". Right now it could show that vacuously.

**Recommendation (small, and in the sidecar — never inside a v0 event, which laws 1–2 leave no room
for):** report the per-page prose-mention count in the **coverage manifest** next to `faultsBySource`,
so the diagnostic can assert **both** halves: *"no prose pin"* (`faultsBySource` has no
`identifier_scan`) **and** *"the scan still sees the prose"* (the mention count is > 0). One number
restores the observability the alignment removed — and it is the difference between a diagnostic that
can fail and one that cannot.

## 3. An erratum on this lane's earlier claim (the "byte-identical" fixture comparison)

`reports/RR-W8CSTEP1-20261111.md` §1 claimed: "the committed live fixture is reproduced ts-stripped
byte-identical by the in-flight code … ts-stripped identical: True". **That comparison was made against
the working-tree copy** — which their in-flight run had *already regenerated* — and it was labelled
"committed" because the label was assumed rather than checked. Against `HEAD`'s true bytes:

```
HEAD's committed package fixture : 20 content lines, faults [identifier_scan, tool_recall, identifier_scan]
the new observer produces          : 18 content lines, faults [tool_recall]
```

So the committed fixture was **not** reproducible by the new observer, and it **needed** regeneration —
which their commit did (without `--force`, in the same commit as the observer change ✓).

**The conclusion survives, for a different reason.** The hazard (law 5, orphaning a frozen drop's
checksum) is still cleared, because: the *package* fixture is **not checksum-pinned anywhere** — the
`live-echo.jsonl` entries in `corpus/m2/checksums.sha256` and `corpus/m8/checksums.sha256` are the
frozen **corpus drops**, a different artefact (22 content lines, carrying the two `identifier_scan`
faults, untouched) — and the two frozen *package* fixtures (`hermes-echo-synthetic.jsonl`,
`hermes-thrash-synthetic.jsonl`) are protected by the generator's own refusal and are never regenerated
by the test suite.

**A bonus of the alignment, worth noting:** the frozen m2 drop is now the only committed artefact that
still shows the **old** observer's behaviour (the prose faults), while the package fixture shows the
**new** one — so the corpus holds the before-picture and the fixture the after-picture, which is a
useful pair for anyone reading the history.

## 4. Executed agent-doings

- Every item was checked at the **committed** bytes (`git show 7e0f2df:…`), not at the working tree, and
  the gate was run with a clean env (`CTXVM_BUDGET_TOKENS` unset) so the env leak could not be mistaken
  for a result.
- The gap was found by asking what the diagnostic will actually be able to assert, not by re-reading the
  plan — and the finding is stated as a *recommendation* on their file, with the one-line reason.
- This lane's own earlier comparison was re-run against `HEAD` and the error recorded as an erratum
  (appended, not rewritten), with the corrected reasoning and the survival of the conclusion.
- Kit: this card + the erratum block on `reports/RR-W8CSTEP1-20261111.md` + LOG row + a day-file line +
  the roadmap's W8C pointer. No file of the other lane's was edited; no spec, schema, corpus, vector or
  umpire byte changed; nothing pushed.
