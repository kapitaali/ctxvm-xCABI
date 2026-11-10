# MASTER PROMPT — W8B experiment (free-model re-run of a closed negative)

Give this to the agent running W8B. It assumes no memory of W8 and no access to our chat. Read all of
it before touching anything.

---

## 0. Role and authority

You run a two-arm context-policy experiment on a **free-tier model**, in three phases, each needing an
explicit go from the owner. You do not redesign the experiment, do not touch `spec/**`, `corpus/**`,
`research/**`, and do not spend beyond the phase you were given.

Repo: `/home/theb/Documents/ctxvm`. Branch `main`. Gate: `bash tools/run-ci.sh` (run it UNPIPED and
capture `$?`). Handoff: `bash tools/check-handoff.sh`.

## 1. The record you inherit (do not repeat it)

W8 was closed on 2026-11-10 as a **negative result** (`design/W8-CLOSURE-20261110.md`):

- A turn-granular keep law cannot act on a single-turn session: every `page.declare` carries `turn: 0`.
- On a 12-turn session the protected floor (53,790) plus scaffold exceeded 24,000, 28,000 and 55,000 —
  zero evictions in all three, request peak 79,960.
- Where a middle exists, the 12-turn shape caps any saving at **5.3%** of session input.
- The one measured pair cost **3.14× tokens and 7.2× dollars** for identical parsed artefacts.
- The extra cache-write volume is real and **UNEXPLAINED**; the engine's message list is excluded
  (append-only request series; a unit test shows byte-identical no-op output).

Therefore: do not re-run the 12-turn shape. It cannot produce a result. W8B uses **20 parts and 20
prompts** so the middle is large.

## 2. Verified and unverified (do not confuse them)

Verified in this repo, today:

```
model id in provider /v1/models        nvidia/nemotron-3.5-super-vl-120b-a12b  (one of 84)
NVIDIA_API_KEY                         present in ~/.hermes/.env (never print it)
catalogue price                        $0.15/1M input, $0.50/1M output, NO cache row
```

**Unverified — the first two phases exist to settle them:** tool-calling support (it is a VL model), the
context window (the provider's model row carries none), and whether "unpaid" holds for this account.
The catalogue prices the model, so *free is an account state (NIM credits), not a model property.*

## 3. Build what is missing (before any model call)

1. **Fixture T-A2** — 20 parts, same generator and shape as `design/w8-tasks/T-A.md` (250 lines per
   part, line lengths uniform in [5,120] bytes, seed 42), materialised into two workspaces
   `experiments/w8b/{ws-naive,ws-paged}`. Do not hand-edit generated files.
2. **Checker** — reuse `tools/w8-checker-ta.py` unchanged: parsed equality is the gate, canonical bytes
   are an observation. It takes `<fixture-dir> <artefact-path>` and prints what it read.
3. **Profiles** — `~/.hermes/profiles/w8b-naive` and `w8b-paged`, copied from the w8 pair, differing in
   exactly two keys: `context.engine` (compressor vs ctxvm) and `plugins.entries.ctxvm-tracer.settings.budgetTokens`
   (absent vs **70000**). Both carry `toolsets: [file]`, `agent.max_turns: 12`, and
   `model.default: nvidia/nemotron-3.5-super-vl-120b-a12b`, `model.provider: nvidia`.
   Verify: `hermes config get toolsets -p w8b-paged` → `- file`.
4. **Driver** — extend `tools/w8-driver.py`: 20 PROMPTS (reads 1–18, parts 19–20 on prompt 19, artefact
   on prompt 20), seal parts 01–03 after prompt 3, `--profile-prefix w8b`, `--expect-budget 70000`,
   and a `prompt digest` (sha256 of the prompt list + artefact spec, 12 hex) stamped into the run dir.

Model, provider and toolset are **profile** settings. Never pass `-m`, `--provider`, `-t` or
`--max-turns` on a named session: the gateway refuses creation overrides on resume
(`Resume retains gateway session policy`), and `--max-turns` fails even on a fresh name.

## 4. Phase 0 — capability (ONE call, ~$0.00–0.001)

```
source tools/w8-run-env.sh w8b-paged "$HOME/.local/state/ctxvm/traces" w8b-probe >/dev/null 2>&1
hermes chat -q "Use the read_file tool to read fixture/part-01.txt and reply with its byte count." \
    --oneshot -c w8b-probe-cap-$(date +%H%M%S) --create-if-missing --in experiments/w8b/ws-paged
```

Record: the reply, the tool calls, the session row, and the provider export delta for the key.

**Stop and report if:** no tool call is made (the model cannot drive the surface), an auth or rate-limit
error appears, or a charge appears that the owner has not approved.

## 5. Phase 1 — shape (THREE prompts, ~$0.02)

Three prompts on one named session: read part-01, read part-02, then "state the running total of long
lines so far".

**Stop and report if:** `len({page.declare.turn}) < 3`, every declare is `turn: 0`, or a request near
90 k tokens is refused for context length. Phase 1 also confirms the real floor; record it.

## 6. Phase 2 — paired cells (4–6 pairs, budget 70,000)

Shape arithmetic you are testing (apx4 estimate, not a measurement):

```
parts 20 × ~15,973 B = 319,460 B ≈ 79,865 tokens
floor ≈ 42,420   (system 5,483 + parts 01-03 11,979 + parts 15-20 24,958)
middle ≈ 43,923  (turns 4-14, parts 04-14)
peak request ≈ 90k  ->  needs a >=128k window (Phase 1 decides)
budget 70,000 -> ~21k evictable, ≈23% of the peak request
```

One cell = one 20-prompt session, `hermes chat -q ... --oneshot -c <name>` per prompt, all via the
driver. Naive and paged run in the same sitting, same model, same surface.

## 7. Acceptance and taxonomy

```
python3 tools/w8-driver.py --capture <capture.jsonl> --expect-budget 70000
```

Verdicts, and they are not interchangeable:

- **DATA-INVALID** — multiple session ids, a shell/code tool used, a **successful** sealed-part read, a
  stale artefact present at start, budget ≠ 70000 or source ≠ settings, coverage/replay non-zero.
  Does not count; is evidence of nothing.
- **NO-OP** — record sound, `evictedTokens == 0`. This is an **outcome** and stays in the denominator.
- **ARTEFACT-FAIL / CEILING** — also outcomes: the model's behaviour on this task.
- **CELL** — evictions > 0 **and** a parsed-equal artefact.

## 8. Cost and the prediction block

The model is cheap or free, not weightless. Before Phase 2, fill and commit the prediction block in
`reports/W8-SPEND.md` §Prediction: expected evictions and turns, expected cache-write share (there is no
cache price row — treat all input as uncached), expected cost range at the catalogue rate, expected
artefact result, and the verdict that would mean an **instrument bug**.

Ceiling: $2.50 for 4–6 pairs. Compute cost from the provider export's `debited_usd` delta for the key,
never from `providerUsage` in the trace — that field reads 3 on a 50 k request.

## 9. Recording (per cell, before asking for the next)

- `reports/W8B-CHUNKLOG.md` — one row per cell.
- `reports/W8-SPEND.md` — ledger row: arm, calls, tokens, cache columns, `debited_usd`, verdict.
- `reports/RR-W8B-<date>.md` — the seven checks, the numbers, the verdict, what it does not prove.
- One LOG row per card, exactly four pipes; commit with explicit paths as
  `kapitaali <teppo@kapitaali.com>`. Never stage another lane's rows; never push.

## 10. Hard stops

```
no tool call in Phase 0                      stop — the model cannot drive this surface
context refusal near 90k                     stop — reduce parts, do not shrink the budget
rate-limit storm (3 consecutive throttles)   stop — a throttled prompt is DATA-INVALID, not a failure
any charge without owner approval            stop
all declares turn 0 in Phase 1               stop — the session collapsed, the shape is void
budget != 70000 or source != settings        VOID at turn 0
shell or code tool in the refs               VOID
a sealed part read that SUCCEEDS             VOID (an attempt that fails is recorded, not fatal)
coverage or replay non-zero                  VOID
```

Also: never restart the gateway mid-cell; never edit the fixture after a result; never re-title a NO-OP
as a paging result; never claim a cost saving.

## 11. What you may claim at the end

Supportable: "at budget 70,000, over n pairs on <model>, the paged arm evicted X tokens, produced a
parsed-equal artefact in m of n, and its receipt was y× the control's."

Not supportable: any saving, any equivalence or non-inferiority, any generalisation to the paid model or
another shape, and any cause for the cache-write volume.

## 12. Eight traps this card already paid for

```
1  -z is one turn; every declare carries turn 0            use a named session across prompts
2  creation overrides are refused on resume                model/provider/toolset live in the profile
3  the CLI --max-turns is unusable                         ceiling = agent.max_turns in the profile
4  a default is not a treatment                            budget from profile settings; verify at turn 0
5  prose is not a seal                                     remove parts 01-03 from the disk
6  turn.render.residentTokens is the flush-time total      use perApiRequest for any per-turn series
7  providerUsage.inputTokens reads 3                       price from the provider export only
8  a checker that hardcodes paths proves nothing           argv only, and it must print what it read
```

## 13. Deliverable at the end of each phase

Five lines: what ran, the calls, the money from the export, the verdict (DATA-INVALID / NO-OP /
ARTEFACT-FAIL / CELL), and the one next action. No prose beyond that.
