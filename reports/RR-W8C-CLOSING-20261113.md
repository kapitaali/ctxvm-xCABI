# RR-W8C-CLOSING-20261113 — what this line measured, what it can attest, and where it stops

Zero spend. Closing card for the W8C line: two booked cells, a failed-then-corrected simulator question,
a measured cross-harness factor, and five instrument defects that each made a working treatment look
inert. Plugin at **0.13.19**.

## The measured results

```
cell-02   free   longcat   20 prompts, budget 60,000   request 0.60× at turn 19, 210,856 evicted
cell-03   paid   luna      same shape                  request 0.57×, cost 2.11×
                                                        (0.1580 vs 0.0748 gateway estimate)
                                                        bill $0.2534, of which 72.2 % cache writes
sim S     turn granularity  FAIL  33.3 % median, +3,200/turn residual
sim S2    point clamp       PASS, then RETRACTED — a 5 % tolerance is below one page (7.4 %)
sim S3    one-page bound    FAIL by 1.003 pages (4,423 vs 4,409); median 1.07 %
```

The policy finding has not moved since cell-03: **the request is held at the budget and the cache pays
for it.** On the free tier that is $0.00; on a paid subject it is 2.11× the control's cost while sending
0.57× of the request. No saving is claimed and none may be.

## The cross-harness factor, now measured

Same six-prompt file-read task: **6 `turn.render` rows on Hermes, 13 on OpenCode** (same model, 18 with a
second free model). A Hermes turn buckets about two requests; an OpenCode turn is a request. Every
measurement above is within-Hermes or denominated in sessions and requests, which is why it survives; any
comparison whose denominator is `turn.render` does not. `call.meta.providerUsage` is 6/6 on Hermes and
0/13, 0/18 on OpenCode, so no cost or cache claim may be made from an OpenCode capture at all.

## What attests what, after five defects

| fact | source | scope |
|---|---|---|
| evicted tokens per turn | `turn.render.evictedTokens` in the trace | per session, per turn |
| which pages left | sidecar `evictedPages` / `evictedPagesCount` | per session |
| per-selection request sizes | sidecar `callSizes` (`before`, `after`, `dropped`) | per session |
| engine installed, entered | sidecar `engineRegistered`, `engineEntered`, `engine` (arm-conditioned) | process |
| selection count | `engineSelectionsProcess` — **process-wide, informational only** | process |

The last row is the line's one admitted weakness. One observer slot serves every session, so a count of
selections cannot be attributed to a capture; three attempts to attribute it (0.13.15, 0.13.16, 0.13.18)
each moved the error rather than removing it, and 0.13.19 labels it honestly instead of pretending. The
verifier no longer depends on it: a treatment is proven by `evictedTokens > 0` in its own trace, and a
control by `evicts nothing` plus `control selects nothing` on the arm-conditioned field.

## The defect chain, recorded because it is the real cost of this instrument

```
0.13.0-1   evictions unreported          the engine rewrote the request and said nothing
0.13.6     observer lost to the clone     the host deepcopies the engine at agent build
0.13.9     entry log through an unimported Path, counter never defined (except: pass)
0.13.12-13 capture read an instance that did no work (module globals fixed it)
0.13.15-18 per-session attribution moved the error three times; label adopted
```

Four of these produced a confident wrong conclusion from me, and one produced a false upstream issue
draft, since deleted. Every one was caught by a check that was written before the result was read.

## Where this stops

The next question is not another measurement of this policy: it is whether a clamp with ~7 % granularity
(evaluated per page, paid for in cache writes) is worth its cost at a *different shape* — cold prefix or
no prefix caching, where the same 203,975 unsent tokens would be priced at the input rate. That is a new
preregistration under the ratified rule, not a continuation, and it needs the owner's decision before any
spend.

## Erratum (2026-11-13, after `RR-W8CCLOSINGREV-20261113` / `02c4fc8`)

The review lane found the mechanical cause of the loss I had attributed to attribution logic, and the
attestation table above was therefore wrong on two rows.

**The bug.** In 0.13.18/0.13.19 `_record_selection` used `_target` at the `call_sizes_by_session` write
and at the `selections_by_session` write, but assigned `_target = _sid` fifteen lines later. Python
compiles `_target` as a function-local, so every call raised

```
UnboundLocalError: cannot access local variable '_target' where it is not associated with a value
```

after `note_evicted` had already run (which is why `turn.render.evictedTokens` survived), and the
`except Exception: pass` swallowed it. Result: `callSizes: []`, `evictedPagesCount: 0`, and
`selections_by_session` empty — while `engineSelections` still showed 41 because the manifest read the
module-global `_selections_total()`. Same class as 0.13.7's unimported `Path`: an `except` that hides its
own cause.

**Fixed in 0.13.20.**

```
_target = _sid is bound FIRST, before tracer_for, note_evicted and every write
manifest: "engineSelections" is per session again; "engineSelectionsProcess" keeps the global
driver: the control check reads the per-session count, never the process-wide one
```

Proven in-process before commit: the callback writes `call_sizes_by_session`, `selections_by_session`
and `evicted_refs_by_session` for the session, with no swallowed exception.

**Rows corrected:** `evictedPages / count` and `callSizes before/after/dropped` were **dead in 0.13.18
and 0.13.19**, not "per session ✓". They are per session again in 0.13.20 and must be confirmed on the
next capture — this erratum does not claim them working, only the code that should make them work.

**What is unaffected:** every headline result. `turn.render.evictedTokens` never depended on this path,
and the cells, the paid bill, the cross-harness factor and the stop on spend all stand.

## Confirmation capture (2026-11-13, plugin 0.13.21)

The first capture in this line where every per-session field is populated together, and the first with
the swallow recorder armed.

```
run              w8b-20261113-150420-paged   CELL   41 calls   864,596 in   523.6 s   $0.00
_swallowed.log   ABSENT — nothing was swallowed during the run
_selections.log  41 lines, one per selection:
                 arm=paged budget=60000 before=95360 after=56358 dropped=9 resident=86806
sidecar          engine 'ctxvm' · engineSelections 16 · evictedPagesCount 9
                 callSizes 16, dropped values 1…9
scorer S3        page 4,411 from dropped == 1 → interval (55,589, 60,000] → PASS, median 0.92 %
```

`engineSelections` now means what it says: **16 selections actually rewrote the request**, out of 41
entries, and it belongs to this session. The 0.13.20 erratum's two rows are confirmed working on live
bytes.

**On the one-page bound, both readings are now on record and neither is retracted:**

```
2026-11-13 12:37 capture   16 of 17 inside, one at 4,423 = 1.003 pages   FAIL by 14 tokens
2026-11-13 15:04 capture   16 of 16 inside                               PASS, median 0.92 %
```

So the honest statement is not "the clamp is exact within one page" but "the clamp is exact within one
page in one capture and missed it by 0.3 % in another" — a page-granular policy whose overshoot depends
on where the page boundary falls. That is the precision a reader should assume.

## Erratum 2 (2026-11-13, after `RR-SHAPEGAP-20261113`)

Two claims in this card, and one in the chat summary of the replay, were overstated. Both are withdrawn
and replaced with what the evidence supports.

**1. "0 stubs in the derived table is independent confirmation that this policy removes pages."** Wrong,
and the review lane is right about why: a slot becomes stubbed only through a `PageEvict`, our adapter
emits none, so `stubbedSlots = 0` is **entailed by the event vocabulary** — it cannot be evidence about
the request. The witnesses for removal are (a) the engine source, which has no stub path at all,
(b) `turn.render.evictedTokens`, and (c) the request-size series. Not the projection.

**2. "Zero divergences in replay is an independent witness."** Partly by construction: the plugin pins the
trace's `residentTokens` to the core's whole-table tally, so the residency half agrees by design. The
replay **is** a determinism and internal-consistency witness — three runs, one hash, and the checks have
teeth (the review lane's mutations produce `residentTokensMismatch` and `renderModeMismatch`, exit 1) —
but it is **not** evidence about the treatment.

**3. And a defect neither of us had noticed, now on record:** on a flush-tail trace the derived page table
is **not turn-scoped**. Every `page.declare` row precedes the `turn.render` block, so the export's
positional cut includes all 21 declares at turn 0 as well as turn 19. The table therefore claims 21 pages /
86,569 tokens where the request carried **12 pages** — and the **provider's own receipts** say the
model saw 56.3 % of the control's tokens, so the removal is real and the **table is the false part**.
*(The 47,805-token figure first written here is cross-capture — 86,569 minus the free capture's 38,764 —
and is withdrawn; the page count and the provider ratio are measured on the paid capture itself.)*

That is a representation gap in v0, not a bug in this line's measurement: `page.evict` requires a
`stubText` a removal policy never has, `evictedTokens` is unchecked in v0, and the derived table is not
turn-scoped. The consequence for the paper's "did vs saw" dichotomy is that a removal policy has no third
branch, and it is written up for the white-paper lane in `RR-SHAPEGAP-20261113` §2.
