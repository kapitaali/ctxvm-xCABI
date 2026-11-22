# RR-E3STAGE0-TIMEOUT-20261122 — Stage 0 call timed out at 300 s: a config/timing issue, not a gate result

Owner "fix the blocker. then go". Stage 0 was launched on `bank-pilot9` after the context-window fix (`-c 16384`,
`RR-E3STAGE0-LAUNCH`), but the **first forced-gold call hit the 300 s client timeout** — no gate was evaluated, no
result recorded. I diagnosed rather than retrying blindly. $0, no provider call, no push.

## 1. What happened (from the server log and harness trace)

- Preflight passed: `n_ctx=16384`, max full-context tokens 8,331, 9 tasks.
- The server cancelled the first task at 300 s. Server log: `prompt processing, n_tokens=2048, progress=0.25,
  t=148.88 s / 13.76 tokens per second` → at ~13.8 tok/s an 8.3k-token prompt needs **~10 minutes**, far past the
  harness's 300 s client timeout. Health stayed 200; the server itself is fine.
- **This is not a G0a–d result** — no gate was reached. The run aborted with a `TimeoutError` before writing
  `stage0-result.json`.

## 2. Why slower than E0

E0's prompts were ~900 tokens (prompt eval ~19 tok/s, 1.5–2 s/call). E3's tasks are ~8.3k tokens — the prereg's
intended 8–9k scale — so each condition calls for a ~10 min prompt evaluation. Four conditions × 9 tasks ≈ 36 calls
would be ~6 hours of prompt evaluation alone. This is the reviewer's stated risk ("small local model may not
retrieve at 8–9k tokens") now showing up as a **timing** cost, not a retrieval failure.

## 3. Fix applied (and one probe pending)

- Raised `TIMEOUT` 300 → **1200 s** in both `stage0-instrument.py` (sha `fd772fbd…`) and
  `stage1-policy-damage.py` (sha `8bc2251e…`); both recompile.
- Started a **bounded single-call timing probe** with a 1,200 s client timeout to confirm a full forced-gold call
  actually completes. Stage 0 will **not** be relaunched until that probe returns (I will not run a second copy
  concurrently).

## 4. What this means for the plan

Even if the probe passes, a full 9-task Stage 0 is ~6 h and the 36-task bank would be ~24 h — far beyond the
"Stage 0 near 2.5 h" estimate, which assumed ~1 min/eval. If the probe is too slow or times out again, the honest
options are: (a) shrink the fixture (the prereg allows "size is parameterizable and shrinkable for a CPU pilot") to
a context the model processes faster, or (b) accept a multi-hour Stage 0. Both are decisions to surface, not to
silently take. No Stage 1, no plugin change, no claim.

## 5. Applied

This card, an append-only LOG row (four pipes), and a day-file section in `reports/RR-DAY-20261122.md`.
