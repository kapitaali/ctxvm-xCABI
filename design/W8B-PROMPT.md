# MASTER PROMPT — W8B experiment (free-model re-run of a closed negative)

Give this to the agent running W8B. It assumes no memory of W8 and no access to our chat.

---

## 0. The two-profile rule (read this before anything else)

W8B needs **exactly two** Hermes profiles, and they already exist:

| profile | role | `context.engine` | extra |
|---|---|---|---|
| `w8bn-naive` | control | `compressor` | — |
| `w8bn-paged` | treatment | `ctxvm` | `plugins.entries.ctxvm-tracer.settings.budgetTokens: 70000` |

Both: model `meituan/longcat-2.5:free`, provider `nous`, `toolsets: [file]`, `agent.max_turns: 6`.

**Never create a profile.** Not with `hermes profile create`, not with `--clone`/`--clone-from`, not by
copying a directory, not by letting a script do it. Every extra profile that ever existed here came from
provisioning one pair per provider or per model — eight were created that way and had to be deleted.
The runner refuses to create one and preflight fails if the count under the prefix is not exactly 2.

Check the state before you run anything:

```
bash tools/w8b-profiles.sh
-> w8bn-naive   engine=compressor  model=meituan/longcat-2.5:free
-> w8bn-paged   engine=ctxvm       model=meituan/longcat-2.5:free
-> OK: the pair differs only in context.engine and the paged budget block

hermes profile list          # both must be listed; a stopped profile cannot serve a session
```

If either check fails, **stop and report**. Do not repair it by creating, deleting, renaming or
re-cloning a profile. That is the owner's call.

## 1. Role and authority

You run a two-arm context-policy experiment on a free-tier model. You do not redesign it, do not touch
`spec/**`, `corpus/**`, `research/**`, and do not edit the runner, the driver, the profiles or the
fixture during a run. You stop and report if the preflight refuses, if a precondition fails, if an arm
returns NO RECORD, or if any charge appears.

Repo `/home/theb/Documents/ctxvm`, branch `main`. Gate: `bash tools/run-ci.sh` (UNPIPED, capture `$?`).
Handoff: `bash tools/check-handoff.sh`.

## 2. The record you inherit (do not repeat it)

W8 closed 2026-11-10 as a **negative result** (`design/W8-CLOSURE-20261110.md`):

- A turn-granular keep law cannot act on a single-turn session: every `page.declare` carries `turn: 0`.
- On a 12-turn session the protected floor (53,790) plus scaffold exceeded 24,000, 28,000 and 55,000 —
  zero evictions in all three, request peak 79,960.
- The one measured pair cost **3.14× tokens and 7.2× dollars** for identical parsed artefacts.
- The extra cache-write volume is real and **UNEXPLAINED**.

W8B exists to give the keep law a **20-part, 20-prompt** shape where a middle actually exists. Measured
on 2026-11-11 with T-A v2: per-turn request **9,141 → 98,934 tokens**, crossing 70,000 around turn 13.
That is the first session in this card with pressure. Do not shrink it.

## 3. What is verified, and what is not

```
model         meituan/longcat-2.5:free   tool calls verified, correct answer, $0.00, ~16 s per prompt
              stepfun/step-3.7-flash:free also verified, but 167 s per prompt — fallback only
auth          OAuth for `nous` copied into both profile homes from the root auth.json
openrouter    unusable: account in debit (401). No profile exists for it, and none may be created.
nvidia        used once, tool-calling verified, but no profile exists for it and none may be created.
```

Still unverified: the context window (no model row carries one) and whether the model holds a pinned
surface across 20 prompts. Prompt 1 decides the second.

## 4. What is already built (do not rebuild, do not edit)

```
experiments/w8b/ws-{naive,paged}/fixture/   20 parts, 250 lines each
~/.hermes/profiles/w8bn-{naive,paged}       the pair (see §0)
tools/w8-driver.py                          20 prompts, seal of parts 01-03 after prompt 3,
                                            preflight asserts, --capture verifier, --limit N
tools/w8-checker-ta-v2.py                   parsed-equality gate, argv only
tools/w8b-run.py                            THE RUNNER: preflight, probe, both arms, bundle
tools/w8b-profiles.sh                       the two-profile check
design/w8-tasks/T-A-v2.md                   the task of record
```

If you believe one of these is wrong, stop and report it. Do not fix it inside a run.

## 5. The precondition — a pair may not start without it

The prediction block (`reports/W8-SPEND.md` §Prediction) says a mismatch between prediction and
verifier is an INSTRUMENT-BUG. So the instrument is shown to engage **first**, with one prompt:

```
python3 tools/w8b-run.py --provider nous --probe
```

Read the three new fields:

```
"engine": "ctxvm" | null
"engineSelections": 0 | n        <- must be > 0 for the pair to start
"precondition": "READY" | "NOT READY — engine never selected; a pair cannot start"
```

**As of 2026-11-11 the answer is: NOT READY.** Measured three ways on the one-shot CLI path — on the
paged profile, on the default profile with `context.engine: ctxvm`, and with the engine class built in a
plain interpreter (`_HOST_ABC: True`) — the host never calls `select_context`: zero selections, sidecar
`engine: null`. `hermes_cli/cli_tui_mixin.py:1833` says why: *"plugins load in the gateway, not here
(PLG-7)"*. See `reports/RR-W8B-ENGINE-20261111.md`.

So: if the probe says **NOT READY**, stop and report. Do not run the pair; it would burn 40 prompts to
produce a VOID that is already known. The two remedies, both owner decisions, are in that card: run the
pair through the gateway, or move selection into the `pre_llm_call` hook.

## 6. How to run, once §5 says READY

```
cd /home/theb/Documents/ctxvm

python3 tools/w8b-run.py --provider nous --dry-run     # preflight + exact commands, writes nothing
python3 tools/w8b-run.py --provider nous               # both arms, 20 prompts each, 120 s cap
```

`--provider nous` selects the model spec, the pair and the auth check. `--model` picks the other Nous
candidate inside the same pair — that is the only way to change subject, because a second profile pair
is forbidden (§0). Do not pass `-m`, `--provider`, `-t` or `--max-turns` to `hermes` directly: model,
provider and toolset are profile settings, and the gateway refuses creation overrides on resume.

If a session cannot be created (`No session found … could not be created`, or
`DeletedWalGenerationError`), the running gateway is holding a stale handle on a profile home that was
deleted and re-created. That needs a **gateway restart by the owner** — do not work around it by
creating or cloning a profile.

## 7. Preflight — not advisory

```
expected exactly 2 profiles matching w8bn-*, found N   (the two-profile rule, §0)
profile missing, or its model/provider differ from the spec
toolsets != [file]                no shell, no code execution
paged budget != 70000             a budget default is not a treatment
fixture does not have exactly 20 parts
a stale artefact.json is in place (archived to the run bundle, never deleted)
gateway started before the installed plugin file
the provider key is missing or does not authenticate (a free provider-endpoint probe)
```

## 8. Verdicts the runner prints

```
| session | calls | in | out | cost | verdict | wall |
```

- **NO RECORD** — the session never flushed. Not evidence of anything.
- **DATA-INVALID** — a record exists but cannot be trusted: multiple session ids, a shell/code tool, a
  successful sealed-part read, budget ≠ 70000 or source ≠ settings, coverage/replay non-zero.
- **VOID** — record sound, but `engineSelections == 0` or `evictedTokens == 0` on the treatment. An
  instrument result, not a paging result; never enters the denominator as a cell.
- **NO-OP** — evictions 0 with the engine demonstrably selecting. An outcome; stays in the denominator.
- **ARTEFACT-FAIL / CEILING** — outcomes: the model's behaviour on this task.
- **CELL** — evictions > 0 **and** a parsed-equal artefact.

The naive arm is the control: expect NO-OP and a checker PASS. The paged arm is the treatment: CELL
requires evictions, which the 98,934-token peak against a 70,000 budget makes plausible.

## 9. Cost

Free tier: measured $0.00 for a full 20-prompt session. **If any charge appears, stop** — the run is not
authorised to spend. Read cost from the session row and the provider export, never from
`providerUsage` in the trace: that field reads 3 on a 50 k request.

## 10. Recording, after the run

The runner writes `~/.local/state/ctxvm/w8-runs/<run-id>/`: `summary.json`, `summary.md`, per-arm
`driver.out`, `driver.err`, `verify.txt`, `checker.txt`.

- append the two rows to `reports/W8B-CHUNKLOG.md` (or re-run with `--record`)
- write `reports/RR-W8B2-<date>.md`: verdict per arm, numbers, cost, what it does not prove
- one LOG row, exactly four pipes, committed with explicit paths as `kapitaali <teppo@kapitaali.com>`
- `bash tools/run-ci.sh` unpiped and `bash tools/check-handoff.sh` before that commit

## 11. Hard stops

```
probe shows no tool call              stop — this model cannot drive the surface
probe shows engineSelections 0        stop — INSTRUMENT-BUG, no pair (§5)
three prompts over 120 s              stop — too slow for this model
repeated "does not exist" errors      the model cannot hold the surface — stop, say so
context refusal near 90k              stop — reduce parts, never shrink the budget
NO RECORD on either arm               report it; do not re-run blindly
auth 401 / 429                        an account or throttle fact, not a code defect
a profile check that is not "OK"       stop — §0; never repair it yourself
any charge                            stop
```

Never restart the gateway mid-run. Never edit the fixture after a result. Never re-title a NO-OP or a
VOID as a paging result. Never claim a cost saving.

## 12. What you may claim at the end

Supportable: "at budget 70,000, over n pairs on <model>, the paged arm evicted X tokens, produced a
parsed-equal artefact in m of n, and its receipt was y× the control's."

Not supportable: any saving, any equivalence, any generalisation to another model or shape, and any
cause for the cache-write volume seen on the paid model.

## 13. The traps this card already paid for

```
1  -z is one turn; every declare carries turn 0          use one named session across prompts
2  creation overrides are refused on resume              model/provider/toolset live in the profile
3  the CLI --max-turns is unusable                       ceiling = agent.max_turns in the profile
4  a default is not a treatment                          budget from settings, verified at turn 0
5  prose is not a seal                                   remove parts 01-03 from the disk
6  turn.render.residentTokens is the flush-time total    use the per-turn request series
7  providerUsage.inputTokens reads 3                     price from the export only
8  a checker that hardcodes paths proves nothing         argv only, prints what it read
9  model prose is not a provider error                   a 429 leaves a log line
10 a key that exists is not a key that works             probe the provider's endpoint
11 a profile carries its own .env                        updating the root key alone changes nothing
12 a provisioning script becomes eight profiles          two is the rule; the runner refuses
13 a model that cannot count will reproduce the file     ask only for what the tool reports
14 a killed CLI orphans a session and nothing flushes    SIGTERM first; a timeout must flush
```

## 14. Deliverable

Five lines: what ran, the calls, the money, the verdict per arm, and the one next action.
