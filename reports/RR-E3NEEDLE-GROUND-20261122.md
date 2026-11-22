# RR-E3NEEDLE-GROUND-20261122 — verified: E3 needle-revisit design is grounded in the real engine; prereg + generator exist, harnesses owed

Review lane, verify-then-record. Subject: the gitignored `experiments/needle-revisit/` workspace (prereg draft +
fixture generator) created by the owner/hermes side on 2026-11-22, grounded in the actual engine source. Zero spend,
no model call, no commit (the workspace is gitignored by `.gitignore:50`). I did not generate the bank, build the
harnesses, or run any stage — that awaits the owner's go.

## 1. Verified against the real product code (the reviewer's stated gap, closed)

| claim | source verified | result |
|---|---|---|
| `select_context` → `_plan` → `_assemble` drops pages with **no stub** | `packages/hermes/live/context_engine.py`: `_assemble` docstring "dropped pairs vanish together"; `removed_results = dropped \| …`; no stub emitted | confirmed — cause #3 is real in the product |
| keep law protects head/tail | `_hard_keep` (`:822–834`): `protect_first_n=3`, `protect_last_n=6`, `keep.update(non_system[:3])` and `[-6:]` | confirmed |
| offline-drivable with synthetic messages | `select_context` (`:422`) takes a message list; engine tests drive it that way (owner's check) | confirmed from the signature and test pattern |
| `floor_bust` when floor reaches budget | `_plan` (`:898–919`) emits `reason: "floor_bust"` | confirmed |
| band lever: turn 1 = head, ~2–21 = evictable middle, ~22–24 = tail | generator `HEAD_N=3, TAIL_N=6`, `isProtectedTurn` (`:27–36`); 24 call/result pairs → indices 2t−1 | internally consistent with `_hard_keep` — a **middle-band needle** is the one at risk |

Note: the generator's band arithmetic (`2*t−1 < HEAD_N` etc.) mirrors the engine's non-system index mapping; I
verified the constants and the `_hard_keep` logic agree, not a full trace-through of every turn index.

## 2. Created artifacts (verified present, gitignored)

- `experiments/needle-revisit/PREREG-E3-NEEDLE-DRAFT.md` (7,824 B) — construct/readout (forced-gold logprob,
  **nats**), the three failure causes it avoids, needle-band stratification grounded in the real keep law, frozen
  Stage-0 gates G0a–d, Stage-1 policy×budget×band damage, Stage-2 stub/drop/naive linkage, a units+bracket
  prediction block, and a result→change table. **Parked on owner go-ahead.**
- `experiments/needle-revisit/generate-needle-bank.mjs` (5,763 B) — deterministic seeded generator;
  `--tasks 36 --pages 24 --lines 26 --seed 7`; 12 early / 12 middle / 12 late; near-duplicate distractor keys,
  one needle per task; schema `e3-needle-v1`. Not yet run (its command needed approval and timed out — no retry).

## 3. Instrument reuse (verified)

The forced-gold mechanism is already proven: `experiments/e0-gate2/run-retry-gates.py` Gate L returned byte-exact
forced text with per-token logprobs (`RR-E0RETRY-RESULT`, `forced_byte_exact=True`), and Gate L passed on both local
models (`RR-E0GATE1`, `RR-E0RETRY-RESULT`). The E3 harness should reuse that mechanism, not rebuild it.

## 4. Go/no-go — recorded for the owner, not executed

The two harnesses are owed: `stage0-instrument.py` (reuse GBNF forced-gold) and `stage1-policy-damage.py` (drive the
real `select_context` offline). Nothing is spent until Stage 0, which needs the server up plus owner approval.
**My recommendation: go** — generate the bank (36 + a 9-task CPU pilot), verify needle-uniqueness/no-leak, then build
Stage 0 and run the frozen instrument gates first. That ordering keeps the reviewer's and meta-diagnosis's shared
lesson: validate the instrument against a planted truth before any hypothesis step. Stage 1 only after Stage 0 passes;
Stage 2 only if Stage 1 shows middle-band damage. No plugin change authorized by this card.

## 5. Scope and applied

No call/spend/commit/push; `research/**` and other lanes' WIP untouched. Applied: this card, an append-only LOG row
(four pipes), and a day-file section in `reports/RR-DAY-20261122.md`.
