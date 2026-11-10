# MASTER PROMPT — W8B experiment (free-model re-run of a closed negative)

Give this to the agent running W8B. It assumes no memory of W8 and no access to our chat.

The work is **one command**. Everything the earlier agents built by hand — fixture, profiles, driver
prompts, seal, verification — is in the repo, and the runner refuses to start if any of it is wrong.
Your job is to run it, read the verdicts, and record them.

---

## 0. Role and authority

You run a two-arm context-policy experiment on a **free-tier model**. You do not redesign it, do not
touch `spec/**`, `corpus/**`, `research/**`, and do not edit the runner, the driver, the profiles or
the fixture during a run. You stop and report if the preflight refuses, if an arm returns NO RECORD,
or if any charge appears.

Repo `/home/theb/Documents/ctxvm`, branch `main`. Gate: `bash tools/run-ci.sh` (UNPIPED, capture `$?`).
Handoff: `bash tools/check-handoff.sh`.

## 1. The record you inherit (do not repeat it)

W8 was closed on 2026-11-10 as a **negative result** (`design/W8-CLOSURE-20261110.md`):

- A turn-granular keep law cannot act on a single-turn session: every `page.declare` carries `turn: 0`.
- On a 12-turn session the protected floor (53,790) plus scaffold exceeded 24,000, 28,000 and 55,000 —
  zero evictions in all three, request peak 79,960.
- Where a middle exists, the 12-turn shape caps any saving at **5.3%** of session input.
- The one measured pair cost **3.14× tokens and 7.2× dollars** for identical parsed artefacts.
- The extra cache-write volume is real and **UNEXPLAINED**; the engine's message list is excluded
  (append-only request series; a unit test shows byte-identical no-op output).

Do not re-run the 12-turn shape. W8B uses **20 parts and 20 prompts** so the middle exists.

## 2. Providers — what is verified, and what is not

| provider | model | profile pair | auth | status |
|---|---|---|---|---|
| **nous** | `meituan/longcat-2.5:free` (recommended) | `w8bn-*` | OAuth in `auth.json` | **tool calls verified, $0.00, 22.5 s** |
| nous | `stepfun/step-3.7-flash:free` | `w8bn-*` | OAuth | tool calls verified, $0.00, **167 s** |
| nvidia | `nvidia/nemotron-3.5-super-vl-120b-a12b` | `w8b-*` | `NVIDIA_API_KEY` | verified end to end; naive arm completed at $0.00 |
| openrouter | `nvidia/nemotron-3.5-lightning:free` | `w8bo-*` | `OPENROUTER_API_KEY` | **401, account in debit — unusable** |

Both Nous ids were verified present on the inference API (397 models listed with the account token)
and both answered a real `read_file` call with the correct byte count. Longcat is 7× faster on the same
call, so it is the recommended subject; stepfun is the fallback.

Still **unverified for every provider**: the context window (no model row carries one) and whether the
model holds a pinned surface across 20 prompts. Prompt 1 of a run decides the second.

## 3. What is already built (do not rebuild, do not edit)

```
experiments/w8b/ws-{naive,paged}/fixture/   20 parts, 250 lines each, parts 01-10 identical to W8
~/.hermes/profiles/<pfx>-{naive,paged}      toolsets [file], agent.max_turns 12,
                                            model+provider per provider; paged carries budgetTokens 70000
tools/w8-driver.py                          20 prompts, seal of parts 01-03 after prompt 3,
                                            preflight asserts, --capture verifier
tools/w8-checker-ta.py                      parsed-equality gate, argv only
tools/w8b-run.py                            THE RUNNER: preflight, both arms, verification, bundle
```

If you believe one of these is wrong, stop and report it. Do not fix it inside a run.

## 4. How to run

```
cd /home/theb/Documents/ctxvm

# 4a. capability probe — ONE prompt, then stop. ~20 s on longcat, $0.00
python3 tools/w8b-run.py --provider nous --model meituan/longcat-2.5:free --probe

# 4b. dry run — preflight + the exact commands, no model calls
python3 tools/w8b-run.py --provider nous --model meituan/longcat-2.5:free --dry-run

# 4c. the run — both arms, 20 prompts each, 120 s cap per prompt
python3 tools/w8b-run.py --provider nous --model meituan/longcat-2.5:free
```

`--provider` selects the model spec, the profile pair and the auth check, and nothing else. `--model`
overrides the id within a provider (that is how the two Nous candidates share one profile pair). Do not
pass `-m`, `--provider`, `-t` or `--max-turns` to `hermes` directly: model, provider and toolset are
**profile** settings because the gateway refuses creation overrides on resume.

Alternative subjects, if the recommended one fails: `--provider nous --model stepfun/step-3.7-flash:free`,
or `--provider nvidia`.

## 5. Preflight — not advisory

The runner refuses, correctly, when any of these is true:

```
profile missing, or its model/provider differ from the selected provider's spec
toolsets != [file]        (no shell, no code execution — the H6 run shelled out 16 times without it)
paged budget != 70000     (a budget default is not a treatment)
fixture does not have exactly 20 parts
a stale artefact.json is in place   (it is ARCHIVED to the run bundle, never deleted)
gateway started before the installed plugin file
the provider key is missing OR does not authenticate   (a free probe of the provider's own endpoint)
```

## 6. Verdicts the runner prints

```
| session | calls | in | out | cost | verdict | wall |
```

- **NO RECORD** — the session never flushed. Nothing to verify; not evidence of anything.
- **DATA-INVALID** — a record exists but cannot be trusted: multiple session ids, a shell/code tool
  used, a **successful** sealed-part read, budget ≠ 70000 or source ≠ settings, coverage/replay
  non-zero. Does not count.
- **NO-OP** — record sound, `evictedTokens == 0`. An **outcome**; it stays in the denominator.
- **ARTEFACT-FAIL / CEILING** — also outcomes: the model's behaviour on this task.
- **CELL** — evictions > 0 **and** a parsed-equal artefact.

The naive arm is the control: expect **NO-OP** (it has no engine) and a checker PASS. The paged arm is
the treatment: **CELL** requires evictions, which the earlier naive session makes plausible (87,578
resident against a 70,000 budget).

## 7. Cost

Both subjects are free: measured $0.00 for a full 20-prompt session on NIM and for the Nous `:free`
models. The nvidia catalogue rate ($0.15/$0.50 per 1M) is only a fallback. **If any charge appears,
stop** — the run is not authorised to spend. Read cost from the session row and the provider export,
never from `providerUsage` in the trace: that field reads 3 on a 50 k request.

## 8. Recording, after the run

The runner writes `~/.local/state/ctxvm/w8-runs/<run-id>/`: `summary.json`, `summary.md`, per-arm
`driver.out`, `driver.err`, `verify.txt`, `checker.txt`.

Then:

- append the two rows it prints to `reports/W8B-CHUNKLOG.md` (or re-run with `--record`)
- write `reports/RR-W8B2-<date>.md`: the verdict per arm, the numbers, the cost, what it does not prove
- one LOG row, exactly four pipes, committed with explicit paths as `kapitaali <teppo@kapitaali.com>`
- `bash tools/run-ci.sh` unpiped and `bash tools/check-handoff.sh` before that commit

## 9. Hard stops

```
probe shows no tool call                 stop — this model cannot drive the surface
three consecutive prompts over 120 s     stop — the shape is too slow for this model
a repeated "does not exist" tool error   the model cannot hold the surface — stop, say so
context refusal near 90k                 stop — reduce parts, never shrink the budget
NO RECORD on either arm                  report it; do not re-run blindly
auth 401 / 429                           an account or throttle fact, not a code defect
any charge                               stop
```

Never restart the gateway mid-run. Never edit the fixture after a result. Never re-title a NO-OP as a
paging result. Never claim a cost saving.

## 10. What you may claim at the end

Supportable: "at budget 70,000, over n pairs on <model>, the paged arm evicted X tokens, produced a
parsed-equal artefact in m of n, and its receipt was y× the control's."

Not supportable: any saving, any equivalence or non-inferiority, any generalisation to another model or
shape, and any cause for the cache-write volume seen on the paid model.

## 11. The traps this card already paid for

```
1  -z is one turn; every declare carries turn 0            use one named session across prompts
2  creation overrides are refused on resume                model/provider/toolset live in the profile
3  the CLI --max-turns is unusable                         ceiling = agent.max_turns in the profile
4  a default is not a treatment                            budget from settings, verified at turn 0
5  prose is not a seal                                     remove parts 01-03 from the disk
6  turn.render.residentTokens is the flush-time total      use perApiRequest for per-turn series
7  providerUsage.inputTokens reads 3                       price from the export only
8  a checker that hardcodes paths proves nothing           argv only, prints what it read
9  model prose is not a provider error                     a 429 leaves a log line; the refusal text did not
10 a key that exists is not a key that works               probe the provider's endpoint in preflight
11 a profile carries its own .env                          updating the root key alone changes nothing
```

## 12. Deliverable

Five lines: what ran, the calls, the money, the verdict per arm, and the one next action.
