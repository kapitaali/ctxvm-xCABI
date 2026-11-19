# RR-FIXBANK-PHASE0-20261119 — content-bearing fixture bank built and validated (Phase 0)

Lane: research. Owner "go" (2026-11-19) for the fixture-bank Phase 0 recommended as the
way forward. **Zero model calls, zero spend.** Phase 0 ran in the DSH sandbox workspace
`tb-dsh-smoke-20261117/fixture-bank/`; the bank was then **landed under
`research/fixture-bank/`** by owner authorization ("include it", 2026-11-19) — synthetic
content is committable, unlike private traces. This is the precondition
`RR-E2HOLD-20261119` names for any E0/E2 reopen: a content-bearing prompt+page bank
paired with valid xCABI traces, stratified on `tool_recall`.

## 1. What was built

`bank.json` — 20 items (`fb01`–`fb20`), each:
- a real task **prompt** (text),
- **11 unique pages** (10 `file` + 1 `tool_result` recall target), each with its actual
  **body text**, `logicalRef`, `contentHash`, `kind`, `tokens`,
- a paired **xCABI trace** (`traces/fbNN.jsonl`) emitted by the real `@ctxvm/node` tracer,
- exactly **1 `tool_recall` fault** on the recall target (pure `tool_recall` stratum; no
  `identifier_scan`), 2 turns.

Totals: 20 items, 220 pages, 20 `tool_recall` faults. The trace stays content-blind
(identities + hashes, per Part III §4.1); the **bank** holds the body text keyed by
`(logicalRef, contentHash)`. So the full context τ = prompt + page bodies, and the ablated
context τ\p = τ with page p's body removed, both exist as actual text — the thing the
frozen corpus could not provide.

## 2. How (real tracer, not hand-written JSONL)

`generate-bank.mjs` imports `createTrace` from
`/home/theb/Documents/ctxvm/packages/node/dist/index.js` (read-only dependency; no
`packages/**` edit). Per item: declare 10 file pages + the tool_result target with real
content; `render()` (turn 0); `recall({tool,args})` + same-content `page()` → the tracer
emits `page.fault(tool_recall)`; `render()` (turn 1); `finish()`. The tracer computes each
`contentHash`/`tokens` from the body, so the trace↔bank pairing is correct by construction.
`buildContext(item, excludeRef)` reconstructs τ / τ\p.

## 3. Verification (commands and results)

```
node generate-bank.mjs                 -> 20 items, 220 pages, stratum=tool_recall
node verify-bank.mjs                   -> 242/242 checks passed, BANK_PHASE0_OK
```

Per item the verifier checks, using the **real** tracer `contentHash`/`approx4`:
- body↔contentHash and body↔tokens integrity;
- every `page.declare` `(logicalRef,contentHash)` matches a bank page;
- ≥1 `tool_recall` fault, all faults `tool_recall`, the recall target is the faulted page;
- ≥10 unique pages; τ non-empty, τ\p shorter, target body absent from τ\p;
- no real-filesystem/bank-path leakage in the trace **or** the model-visible τ/τ\p.

Across the bank:
- `python3 spec/rfc-0.1/validate_schema_v0_1.py traces/*.jsonl` → `OK: all checks passed`
  (the tracer emits `schemaVersion: 0.1`; the v0 validator would reject it — law 1).
- `rust/target/release/replay traces/fbNN.jsonl` → exit 0, `divergences: []` for all 20
  (the single `faultOfResidentPage` violation per trace is the expected tool_recall waste
  signal, not a replay divergence).

## 4. What this unblocks

- **E0** (open-weight page ablation, compute-only): τ\p now exists as text, so leave-one-out
  on output probabilities is constructible. Needs an open-weight model + compute route
  (owner decision; not run here).
- **E2** (hosted ablation): the content precondition is met; a reopen still needs the
  ratified option-(b)/3-sample design, a named model snapshot, a smoke receipt, and a fresh
  owner cost-ceiling sign-off (`RR-E2HOLD`). **Still $0 / parked.**

## 5. Limitations (stated plainly)

- **Synthetic content, not real sessions.** The bodies are generated documentation text;
  no claim about real-task difficulty or ecological validity.
- **No answer-key or grader here.** Phase 0 provides content-bearing contexts; the task
  answer-key, the answer-change equality rule, and the noise floor are defined in the
  E0/E2 prereg, not in this bank.
- **One shape:** a double-fetch `tool_recall` on a resident page across 2 turns. It does
  not exercise eviction, multi-turn thrash, or page interactions (Part II §12.1 threats).
- The `tool_recall` fault is a re-call of an unchanged page; it is the E1-positive label
  stratum, but E1's identifier_scan negative result is unrelated and not pooled.
- No model call, no spend, no plugin install, no wire/corpus change, no commit, no push.

## 6. Deviation

- **D-1:** the first leakage regex flagged the synthetic `agentId` "fixture-bank-fbNN" as a
  leak (false positive). Corrected to target real filesystem/bank paths and to also test
  the model-visible τ; re-run → 242/242. No bank content changed.

## 7. Owner decisions this surfaces

1. RESOLVED 2026-11-19: owner authorized tracking ("include it"); landed under
   `research/fixture-bank/`.
2. E0 compute route (open-weight model + GPU) — separate ruling.
3. E2 reopen cost ceiling + prereg approval — still parked at $0.

## 8. Artifacts

`generate-bank.mjs`, `verify-bank.mjs`, `bank.json`, `traces/fb01–fb20.jsonl`,
`logs-generate.txt`, `logs-verify.txt`, this note, `manifest.sha256`.

## 9. Note to the review lane

Landed under `research/fixture-bank/` by owner authorization ("include it", 2026-11-19);
the commit carrying this card is the landing. Research-lane property; no other lane's
byte staged. Please record the books this lane cannot write:

- **LOG.md** — one append-only row, four pipes, no CJK, e.g.
  `| RR-FIXBANK-PHASE0-20261119 | fixture-bank | Content-bearing tool_recall fixture bank (20 items x 11 pages) built via the real @ctxvm/node tracer and landed under research/fixture-bank/; 242/242 Phase 0 checks, RFC-0.1 schema PASS, replay 0 divergences, deterministic manifest; unblocks E0/E2 content precondition; E0/E2 still owner-gated, $0 spend |`
- **RR-DAY-20261119.md** — a day section summarizing the landing.
- **PROJECT-STATE.md** — research line: fixture bank Phase 0 done and landed; E0/E2 remain
  owner-gated (E0 compute route; E2 cost ceiling). No "E2 ready to run" implication.

Re-derive from the repo location (zero spend):

```
cd research/fixture-bank
sha256sum -c manifest.sha256                 # 24/24 OK
node verify-bank.mjs                         # 242/242, BANK_PHASE0_OK
python3 ../../spec/rfc-0.1/validate_schema_v0_1.py traces/*.jsonl   # OK
../../rust/target/release/replay traces/fb01.jsonl                  # divergences []
```

Scope guard for the books: this is a **synthetic content precondition**, not an experiment
result. No model call, no spend, no E0/E2 GO, no plugin/paper parity, no cost-saving or
model-quality claim. The bank provides τ/τ\p as text; the answer-key, grader and noise
floor belong to a future E0/E2 prereg. Nothing here is pooled with E1, M1, M2 or M3.

