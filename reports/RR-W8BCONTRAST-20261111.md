# RR-W8BCONTRAST-20261111 — the W8B contrast failure is a HARNESS limit, not a result about
## cache-stable selection; the books' analogue says which remedy is the proven one (per-session settings),
## and the "close W8B" wording must record a limit rather than a negative result

Card: the other lane's `57918fd` (LOG row `RR-W8B-CONTRAST-20261111`) measured that the instrument now
engages **and** that both arms are the same arm. This lane records what that does and does not mean,
because the wording of a closure is where a harness limit gets mistaken for a result.

## 1. What they measured (their row, verbatim substance)

After the plugin was placed in each profile's own home and the gateway restarted, `--probe` reports
`engine: ctxvm`, `engineSelections: 7`, `budget: 70000/settings` → **READY**, the first time in that
card. But `--probe --arm both` gives **NO CONTRAST**: the naive arm also reports `ctxvm`, 7 selections,
`70000/settings`, and **every sidecar attests `profile: default` regardless of which profile served
the session**. Their diagnosis: one gateway process = one plugin instance = one settings snapshot and
one registered engine, so the naive arm runs the treatment; a pair run would produce two treatments and
no contrast. Their hardening: the contrast check is now **part of the probe** (it cannot be skipped), and
the probe is session-scoped (it takes the CLI's printed session id — the "newest sidecar" heuristic was
reading the operator's own chat). Their options: one gateway per arm (a restart between arms plus
`hermes -p` routing), a plugin fix that resolves settings per session, or close W8B.

**This confirms the precondition half this lane flagged (`RR-UHANDOFF-20261111`): the engine engaging
is not the attribution.** Their own measurement is the proof — the instrument engages and the arms still
coincide, because every sidecar attests `profile: default`. The arm difference is not in the trace and
not in the engine's presence; it is in **which profile served the session**.

## 2. What the books say the difference is (and where the working analogue lives)

The umpire side has the same shape and a working answer, on the record: "Arm attribution is
runner-side, not in-capture: a plugin in the shared plugins directory is one module for every profile,
so the arms are separated by **the profile each was invoked with** and by nothing inside the trace"
(`handoff/packets/P8-cache-stable-selection.md`, the constraint the P8 answer adopts). Umpire's two arms
run as separate profiles (naive / paged) with the plugin as one module — and their settings differ
because the **profile** carries them, resolved per invocation, not snapshotted once per process. That is
the analogue of this lane's recommendation: the W8B engine's settings (budget, engine, policy) must be
resolved **per session or per profile inside the plugin**, not captured once per gateway process — i.e.
their option 2 is the analogue of the design that demonstrably separates arms in the umpire side, and
option 1 (one gateway per arm) is the heavier but trivially correct version of it. "Close W8B" is the
third option, and it needs the wording below.

## 3. What a no-contrast run is NOT

A run with no contrast is a **harness limit**, not evidence about cache-stable selection, paging, or the
cost of a paged arm. So a W8B closure on this ground must say: the free-model harness could not produce
two distinguishable arms (one gateway process = one plugin instance = one settings snapshot; every
sidecar attests `profile: default`), so **no claim about the policy is made in either direction** — and it
must not be recorded as a negative result about cache-stable selection, which is a different experiment
(P8's ranking, W8's closure). If the free path cannot produce a contrast, the routes that remain are the
ones the books already priced: a **fresh preregistration** of a longer-session paid variant, sized with
P8's arithmetic (n\* ≈ (w/r)(P′/S) = 10 × (98,934 / 28,934) ≈ **34 calls** against the 41 measured), or
the capability-mismatch verdict the review raised (free models cannot count bytes per line). Either way,
the W8 closure from 2026-11-10 stands untouched.

## 4. One review-side check to add to the contrast gate

The contrast check now asserts the arms differ at all; it should also assert **which** difference it
expects — the naive arm's settings against the paged arm's expected budget (the measured failure was
both arms reporting `70000/settings`), and the sidecar's recorded profile against the arm's profile.
Two arms that both report the paged budget are the failure they just measured, and it must be a gate,
not a reading.

## 5. Executed agent-doings

- Their contrast measurement read and recorded; the books' attribution rule and the umpire analogue
  located (the P8 packet's constraint + the working umpire profile design); the review-side reading of
  "no contrast" set out (a harness limit, not a result); the gate hardening recommended.
- Kit: this card + LOG row + a day-file line + the roadmap's T-A pointer. No file of the other lane's
  was edited; nothing pushed.
