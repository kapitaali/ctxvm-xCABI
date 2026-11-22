# RR-E3NEEDLE-BUILD-20261122 — verified: needle bank generated + both harnesses built (gitignored); two blockers before Stage 0

Owner "go" authorized generating the fixture and building the two harnesses (Stage 0 explicitly needed separate
approval). Review lane, verify-then-record. All artifacts are in the gitignored `experiments/needle-revisit/`
workspace (`.gitignore:50`); no repo file, model call, or spend from this lane.

## 1. Generated bank (verified structurally)

- `generate-needle-bank.mjs` (sha `76b4ad35…`, `node --check` OK), seeded `--seed 7`, `--pages 24`, `--lines 26`:
  - `bank-36.json` (sha `bfc6ce39…`): 36 tasks, 12 early / 12 middle / 12 late.
  - `bank-pilot9.json` (sha `dbfaba69…`): 9 tasks, 3/3/3 for the CPU pilot.
- Structural checks (Python): **exactly one needle-key occurrence per task**, gold value on the needle page, needle
  turn in the correct band (early=1, middle 2–21, late 22–24), **zero problems** in either bank. Band mapping matches
  `_hard_keep` (head 3 / tail 6) verified earlier (`RR-E3NEEDLE-GROUND`).

## 2. Built harnesses (verified compile + real-engine smoke)

- `stage0-instrument.py` (sha `49746323…`): reuses the proven GBNF forced-gold per-token logprob mechanism; 4
  conditions/task (full / needle-removed / seeded random-equal-size-removed / repeat); frozen G0a–d gates; writes
  `stage0-result.json`. **Hard preflight** tokenizes the full context and refuses if `n_ctx` too small.
- `stage1-policy-damage.py` (sha `dbe13b2f…`): drives the **real**
  `packages/hermes/live/context_engine.py::CtxvmFaultPinEngine.select_context` offline via a structural host-ABC stub
  (the plugin test's pattern) with the arm pinned, so the engine isn't inert; policies keep-law/recency/random-middle/
  touch-aware/oracle/anti-oracle × 80/60/40% budgets; report-only, no gate; gated on Stage 0 PASS.
  Smoke-tested: real engine builds (head 3, tail 6); `select_context` on a tiny tx returns `None` as expected.

## 3. Two blockers before Stage 0 — surfaced, not papered over

1. **Context window:** `/tokenize` measured a full task at **8,279 tokens** (right at the prereg's 8–9k target), but
   the pinned server runs `-c 2048` — it would truncate and invalidate G0a. Stage 0's preflight will REFUSE. Running
   Stage 0 requires restarting the pinned binary with `-c >= ~8,400` (binary `0f60e048…` and weights unchanged — a
   context-flag change, not a model change). That is a decision for the owner, recorded here.
2. **Stage 0 needs separate owner go-ahead** — the "go" was for fixture + harnesses only. I did not run Stage 0.

## 4. What is not claimed

No Stage 0/1 result, no hypothesis/ρ/paging/cost/quality claim. The E0 double negative stays published; E2 closed;
D17 held. No plugin change. Research/dsh WIP untouched; no push. Applied: this card, an append-only LOG row (four
pipes), and a day-file section in `reports/RR-DAY-20261122.md`.
