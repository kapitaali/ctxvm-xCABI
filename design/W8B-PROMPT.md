# MASTER PROMPT — W8B experiment (free-model re-run of a closed negative)

Give this to the agent running W8B. It assumes no memory of W8 and no access to our chat. Read all of
it before touching anything.

---

## 0. Role and authority

You run a two-arm context-policy experiment on a **free-tier model**. It is **one command** now — the
runner does both arms and verifies them. You stop and report if the preflight refuses, if an arm returns
NO RECORD, or if any charge appears. You do not redesign the experiment, do not touch `spec/**`,
`corpus/**`, `research/**`, and do not edit the runner during a run.

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

## 3. What is already built (do not rebuild, do not edit)

```
experiments/w8b/ws-{naive,paged}/fixture/   20 parts, 250 lines each, parts 01-10 identical to W8
~/.hermes/profiles/w8b-{naive,paged}        model nemotron, provider nvidia, toolsets [file],
                                            agent.max_turns 12; paged carries budgetTokens 70000
tools/w8-driver.py                          20 prompts, seal of parts 01-03 after prompt 3,
                                            preflight asserts, --capture verifier
tools/w8-checker-ta.py                      parsed-equality gate, argv only
tools/w8b-run.py                            THE RUNNER: both arms, verification, bundle
```

If you believe one of these is wrong, stop and report it. Do not fix it inside a run.

## 4. The run

```
cd /home/theb/Documents/ctxvm
python3 tools/w8b-run.py --dry-run                      # preflight + the exact commands, no calls
python3 tools/w8b-run.py --provider nvidia              # nemotron-3.5-super-vl-120b-a12b via NIM
python3 tools/w8b-run.py --provider openrouter          # nemotron-3.5-lightning:free via OpenRouter
```

`--provider` decides three things and nothing else:

```
nvidia       model nvidia/nemotron-3.5-super-vl-120b-a12b   profiles w8b-{naive,paged}
openrouter   model nvidia/nemotron-3.5-lightning:free       profiles w8bo-{naive,paged}
```

Each provider has its own profile pair, because model and provider are PROFILE settings (the gateway
refuses creation overrides on resume). The pair for a new provider is provisioned on first use by
copying the other one, so the two differ in model and provider only — which is the only reason their
results can be compared at all. The runner prints every profile it provisions.

The preflight is not advisory. It refuses, correctly, if any of these is true:

```
profile missing, toolsets != [file], model != nemotron, provider != nvidia
paged budget != 70000
fixture does not have exactly 20 parts
a stale artefact.json is in place   (it is ARCHIVED to the run bundle, never deleted)
gateway started before the installed plugin file
```

A stale artefact is moved to `~/.local/state/ctxvm/w8-runs/<run-id>/stale/` — the previous run's output
is evidence.

## 5. Verdicts the runner prints

```
| session | calls | in | out | cost | verdict | wall |
```

- **NO RECORD** — the session never flushed. Nothing to verify; not evidence of anything.
- **DATA-INVALID** — a record exists but cannot be trusted: multiple session ids, a shell/code tool
  used, a **successful** sealed-part read, budget ≠ 70000 or source ≠ settings, coverage/replay
  non-zero.
- **NO-OP** — record sound, `evictedTokens == 0`. An **outcome**; it stays in the denominator.
- **ARTEFACT-FAIL / CEILING** — also outcomes.
- **CELL** — evictions > 0 **and** a parsed-equal artefact.

The naive arm is the control: expect **NO-OP** (no engine) and a checker PASS. The paged arm is the
treatment: **CELL** requires evictions, which the previous naive run makes plausible (87,578 resident
against a 70,000 budget).

## 6. Cost

Free tier on both providers: $0.00 measured for a full 20-prompt session on NIM, and a `:free` model on
OpenRouter. The NIM catalogue rate is a fallback ($0.15/$0.50 per 1M). If a charge ever appears, stop —
the run is not authorised to spend. Read cost from the session row and the provider export, never from
`providerUsage` in the trace (it reads 3 on a 50k request). OpenRouter free models throttle by
requests-per-minute: a 429 there is real, and the driver's abort will show it as DATA-INVALID.

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
