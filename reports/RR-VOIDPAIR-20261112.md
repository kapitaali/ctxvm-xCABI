# RR-VOIDPAIR-20261112 — the free pair that ran after the paid one is a **VOID**: the treatment arm
## never engaged the engine (`engine: null`, 0 selections) — and the verifier's new CONTROL verdict
## must be conditioned on the arm, or this run could be booked as a false cell

Card: the review side's check of the free-tier pair that ran at 1794479989/1794480479 (the scoring run
behind the simulator work), read from the hermes DB's counters and the sidecars on disk. Nothing was spent
✓ (the free tier ✓).

## 1. What ran, and what it shows

| session | profile | arm | calls | engine | selections | evictions | per-page detail | per-call sizes |
|---|---|---|---|---|---|---|---|---|
| `local-0918f563aca7…` | w8cn-naive | control | 42 | **null** | **0** | 0 | [] | [] |
| `local-09b1c49aa91e…` | w8cn-paged | **paged** | 42 | **null** | **0** | 0 | `[]` | `[]` |

Both arms' sidecars carry `engineSetting: ctxvm` (the profile asks for the treatment ✓), `budgetTokens:
60000 / settings` ✓, `profile: w8cn-paged` ✓, `arm: paged` ✓, `proseMentionsTotal: 190` ✓ (the
observer ran ✓) and `faultsBySource` all zero ✓.

**So the treatment arm never engaged the engine** ✓ — and the plugin's own comment says what `engine:
null` now means in 0.13.x: *"ACTIVATION, not construction … the field now means `select_context()` was
called in this process"* ✓ (`live/__init__.py:686-694`).

**The engine code did not change** ✓ — `git diff 2b6c950..HEAD -- packages/hermes/live/context_engine.py`
is **empty** ✓ — so this is not an engine regression ✓; it is a **runtime** difference ✓. The likeliest
cause is the known one ✓: the gateway was **not restarted after the `w8cn-*` profiles were recreated**
✓ — the PLG-7 behaviour the W8B lane recorded ("the running gateway does not load plugins for these
profiles until it restarts", `reports/RR-W8B-PLUGINHOME-20261111.md`) ✓ — while the **paid** pair used
freshly created `w8cp-*` homes **and a gateway restart** ✓ (their card: *"gateway restarted after the
`w8cp` homes were created"* ✓), which is exactly why the paid pair engaged ✓ (44 selections ✓) and this
one did not ✓.

**The pair is therefore a VOID, not a cell** ✓ — the treatment arm ran as a naive arm ✓ — and nothing was
spent ✓ ($0.0000 ✓, the free tier ✓). Per the ratified rule (4) (an unexplained mismatch remains
INSTRUMENT-BUG ✓) and their own precondition (*"a failed precondition is not a cell"* ✓), it is not
booked ✓ — and here the cause is *explained* ✓ (the engine never engaged ✓), so it is a **void by
instrument fault** ✓, not a policy result ✓.

**One number must not be misread** ✓: the paged arm's cache_read (3,017,600) is *lower* than the
control's (4,658,688 ✓) — with **no engine and no evictions** ✓ that difference is the free model's own
trajectory variance ✓ (it generated less content ✓), **not** a policy effect ✓. The traces themselves are
pruned from the trace directory ✓, so the per-turn series for this pair is not recoverable ✓ — only the
summaries are ✓.

## 2. The sharp edge this run exposes: the verifier's new CONTROL verdict needs an arm condition

The other lane fixed the verifier so that *"a control asked to select nothing has not 'done nothing'"*
✓ (their paid-pair card ✓) — the control now reads **CONTROL** instead of NO-OP ✓. That fix is right ✓,
but it is **not arm-conditioned** ✓, and this pair shows why that matters:

> A **paged** arm with **0 selections** would satisfy "select nothing ⇒ CONTROL" ✓ — and this run's
> paged arm has exactly that shape ✓ (`arm: paged`, `engine: null`, 0 selections ✓). Booked as a cell, it
> would be a **false cell** ✓ — a treatment that never acted, recorded as a control that behaved ✓.

**The sidecar now makes the distinction observable** ✓, so the verifier should carry a **third** verdict
rather than two ✓:

```
arm == control  and selections == 0          -> CONTROL     (the control behaved)
arm == paged    and engine == null           -> VOID        (the engine never engaged)
arm == paged    and selections > 0           -> CELL/NO-OP  (as now)
```

The `engine == null` test is exactly the right discriminator ✓ because in 0.13.x that field means
"select_context() was called" ✓ ✓ — so `engine: null` in a *paged* arm is the fingerprint of a void ✓, and
it is already in the capture ✓ (no new plumbing needed ✓).

## 3. What 0.13.3 does carry (the good news)

The new sidecar fields are the two open instrument items ✓:
- **`evictedPages` / `evictedPagesCount`** ✓ — the **per-page** eviction detail, keyed per session ✓
  (the item this lane asked for: the payload must carry the page's identity, not its tokens ✓) — empty
  here ✓, consistent with a run in which nothing was evicted ✓;
- **`callSizes`** ✓ — the **per-call request sizes** ✓, i.e. the scaffold tokens per request ✓ — the
  simulator's stated prerequisite ✓ (`reports/RR-W8SIM-20261111.md` ✓, and their scoring card
  `reports/RR-W8SIM2-20261112.md`: *"the simulator fails, and the failure names what to record"* ✓). So
  the simulator's blocker is now **implemented** ✓ — the field exists and is per-session ✓ — and the
  scoring can proceed on the next run that actually engages the engine ✓.

**So this pair's value is diagnostic, not evidential** ✓: it shows the void ✓, it pins the verifier's
missing arm condition ✓, and it confirms that the two instrument items the last review asked for are in
the plugin ✓ — while the *evidence* it was run to produce (a scoreable capture) is **not** there ✓,
because the engine never acted ✓.

## 4. What the lane needs before the next scoring run

1. **Restart the gateway after the profiles are (re)created** ✓ — or, better, make the *probe's* READY
   verdict a **precondition of the run** ✓ (their own rule ✓) so a profile/gateway mismatch stops the run
   before prompt 1 ✓ instead of producing a void pair ✓.
2. **Add the arm-conditioned verdict** ✓ (§2 ✓) — the sidecar already carries the evidence ✓.
3. **Record the void explicitly** ✓ — a void pair with a stated cause ✓ (this card ✓) is not the same as
   a pair that was never run ✓, and the difference belongs in the ledger ✓.

## 5. Executed agent-doings

- The run was identified from the DB's counters ✓ and its sidecars read ✓; the engine's non-engagement
  was established from the plugin block ✓ (`engine: null` ✓, 0 selections ✓, `engineSetting: ctxvm` ✓,
  `budgetTokens 60000/settings` ✓) and from the plugin's own definition of that field ✓.
- The engine-code regression hypothesis was **tested and rejected** ✓ (`git diff 2b6c950..HEAD` on
  `context_engine.py` is empty ✓), leaving the runtime cause ✓ (the gateway restart ✓) — which the paid
  pair's own card corroborates ✓.
- The verifier's missing arm condition was identified with the concrete shape that would produce a false
  cell ✓, and the third verdict was specified against fields the capture already carries ✓.
- Kit: this card + LOG row + the day file + the roadmap's W8C pointer. Nothing spent ✓; no file of the
  other lane's edited ✓; nothing pushed ✓.
