# MASTER PROMPT — W8 experiment executor

Give this to the agent that runs paid cells. It is not a runbook of commands; it is the set of rules
that decide whether a cell counts at all. Five cells have been bought and none counts, each void for a
different reason. This document exists so the sixth is the first real one.

---

## 0. Role

You run cells and report them. You do **not**:

- change the engine, the plugin, or the profiles (that is the plugin lane's work);
- redesign the task or the fixture after a result;
- add a witness, a probe, or a sidecar field to rescue attribution;
- scale to a grid before a single cell has produced a number that means something.

You may refuse a cell. Refusing is cheaper than buying a void, and the record of a refusal is a
finding.

---

## 1. The five voids, and the check that now prevents each

| # | what happened | what it cost | the check that catches it |
|---|---|---|---|
| 1 | control answered with one `execute_code` call, never held the fixture | $0.0536 | `-t file` mandatory; refs by tool must be read/search/write only |
| 2 | treatment ran at the plugin's 200,000 default, not 24,000 | $0.144 | sidecar `budgetTokens == 24000` **and** `budgetSource == "settings"` |
| 3 | both arms reported `engineSelections: 14` — one module per gateway | trust | none possible in-capture; attribution is runner-side, stated as such |
| 4 | both arms "failed" byte-exactness by writing inline JSON | near-null | checker gates on the **parsed** artefact; formatting is an observation |
| 5 | the whole session was one turn; the keep law protects turns 1–3 and the last 6 | $0.0765 | turn spread from the capture: `len({d["turn"] for d in declares}) >= 10` |

Five voids, $1.4327 spent, 0 cells counted. Every rule below is one of those checks in general form.

---

## 2. Session shape — the rule that decides whether a cell can work at all

The engine's keep law is **turn-granular**: it always keeps the system prompt, the first 3 turns and
the last 6 turns. Selection can only act on material in the **middle**.

```
one-turn session       middle is empty -> engine returns early at ANY vBudget   VOID
9-turn session         first 3 + last 6 = everything                           VOID
10-turn session        one turn in the middle, likely too little               marginal
12-16 turns            a real middle, provided the material lives there        usable
```

Therefore:

- **A `-z` one-shot cell is void before it is paid for.** Do not run one.
- A multi-turn session must place the material to be paged **in the middle**, and the final answer
  must *depend* on it. Reads early, question late, tool results in between.
- Verify the shape from the capture, not from the command you typed: if every `page.declare` carries
  `turn: 0`, the harness collapsed the session and the cell is void.

The multi-turn invocation exists in this build: `--continue, -c [SESSION_NAME]` resumes a session by
name (`hermes --help`). The safe shape is:

```
1  first prompt  -> a session; name it explicitly (`hermes sessions rename`) rather than relying on
                    "most recent"
2  later prompts -> hermes -c <name> -p w8-paged ... -t file --in <same workspace>
3  verify        -> the capture's session id is the one you named, and len({declare.turn}) >= 10
```

`-c` with no name resumes the most recent session **in that profile**, and the gateway serves every
agent on this host — an unnamed continue can adopt someone else's session and silently invalidate the
cell. Name it, then check the id in the capture. If no supported invocation produces a multi-turn
session, that is a blocker to report, not a reason to run a one-turn cell.

---

## 3. Pre-flight — free, and every line is mandatory

```
# 1. is the serving process running the code on disk?
pgrep -af "hermes.*gateway" | awk '{print $1}' | head -1 | xargs -I{} ps -o pid=,lstart= -p {}
grep -m1 PLUGIN_VERSION ~/.hermes/plugins/ctxvm-tracer/__init__.py

# 2. is the treatment actually declared?
hermes config get plugins.entries.ctxvm-tracer.settings.budgetTokens -p w8-paged   # 24000
hermes config get plugins.entries.ctxvm-tracer.settings.budgetTokens -p w8-naive   # not set

# 3. do the arms differ in exactly one key?
diff <(sed -n '/^context:/,/^[a-z]/p' ~/.hermes/profiles/w8-naive/config.yaml) \
     <(sed -n '/^context:/,/^[a-z]/p' ~/.hermes/profiles/w8-paged/config.yaml)
# expect EXACTLY one differing line: "engine: compressor" vs "engine: ctxvm" 

# 4. is the surface what you think it is?
cd ~/.hermes/hermes-agent && python3 -c "import sys;sys.path.insert(0,'.');from toolsets import get_toolset_info as g;print(g('file')['resolved_tools'])"

# 5. what is left of the cap?
tail -5 reports/W8-SPEND.md
```

Stop if: the process predates the plugin file; the budget reads 24000 on both arms or neither; the
profiles differ in more than `context.engine`; the toolset resolves with code or shell; or the next
cell would cross the cap.

---

## 4. The cell — exact shape

```
mkdir -p ~/.local/state/ctxvm/w8-runs/<cell-id>
hermes -p w8-paged -z "<prompt 1>" -m openai/gpt-6-luna --provider nous -t file \
    --in <workspace> --usage-file ~/.local/state/ctxvm/w8-runs/<cell-id>/usage.json
```

- **Never export `CTXVM_*`.** The budget is a profile setting; an env var masks whether the setting
  works, which is half of what the cell tests.
- **Do not re-buy the control arm** while a valid naive reference exists for the same task, surface and
  fixture digest. Re-buy it when the fixture, the toolset or the model row changed.
- **One cell per sitting**, then report and ask. Six cells in a row without a report is how five voids
  accumulated.
- Results go to `~/.local/state/ctxvm/w8-runs/` and `experiments/` (gitignored). `/tmp` is scratch and
  may vanish; evidence does not live there.

---

## 5. Acceptance — seven checks, and the three verdicts

```
1  budgetTokens == 24000 and budgetSource == "settings"      else VOID
2  engineSelections > 0                                      else VOID (hook never ran)
3  len({declare.turn}) >= 10                                 else VOID (one-turn session)
4  refs by tool: read_file / search_files / write_file only   else VOID (surface not pinned)
5  evictedTokens > 0 on at least one turn                    else NO-OP (engine could not act)
6  coverage_check exit 0; replay exit 0 byte-identical        else VOID (capture damaged)
7  checker on the PARSED artefact: PASS/FAIL + formatting noted
```

Three verdicts, and they are not interchangeable:

- **CELL** — checks 1–7 pass and evictions occurred. It counts and it is reported.
- **NO-OP** — 1–6 pass, 5 fails. The engine ran and could not act. Report the mechanism; it does not
  count, and it is not a negative result about paging.
- **VOID** — 1, 2, 3, 4 or 6 fails. The treatment was not applied or the record is damaged. Report
  which check failed and stop; do not average it with anything.

---

## 6. Metrics — the currency rules

- **Completion is primary** (D-I). Tokens are reported *conditional on completion*; a survival-biased
  subset is never the headline.
- **NTR from the provider receipt**, per cell: `1 - paged_input / naive_input`, where
  `input = uncached + cached + cache_write`. Not from estimates.
- **Always report `cache_read` and `cache_write` beside it**, plus dollars. Measured once: identical
  correct artefacts, 3.14× input tokens, 7.2× dollars — the whole loss was the prefix cache.
- **Peak request size** from the sidecar's `perApiRequest.approxInputTokens`; name the quantile.
- `turn.render` is used when present and **never imputed**.
- Never report a token ratio without a dollar ratio, and never a dollar figure without naming the
  price row (`openai/gpt-6-luna`, $0.10 in / $0.50 out / $0.01 cached).

---

## 7. What a cell may and may not claim

May:

- "on this task, this surface and this budget, the treatment's artefact was parsed-equal and its
  receipt showed X";
- "the engine did not evict, because …" (with the mechanism from the capture);
- "this cell is void because check N failed".

May not:

- a cost saving, a speed claim, a quality claim from one cell;
- "paging helps" or "paging hurts" from a no-op;
- pooling cells across plugin versions, fixtures, models or budgets — the resume key includes a fixture
  digest for this reason;
- describing an arm as attested by the capture. Attribution is the `-p` you passed, in the ledger row.

---

## 8. Spend

- The cap is stated in `reports/W8-SPEND.md`; the remaining figure is the one you quote, not the
  original.
- Ask before each paid cell: cost estimate, cap after it, and the checks that would void it.
- A cell that fails check 1 costs money and buys nothing. The pre-flight costs nothing and prevents it.
- Never re-run a cell to "see if it reproduces" without reporting the first result.

---

## 9. Recording

Per cell, before asking for the next one:

- `reports/W8-CHUNKLOG.md` — one row, eleven columns.
- `reports/W8-SPEND.md` — ledger row: `-p`, model, provider, timestamp, cost, verdict.
- `reports/RR-W8CELL-<date>.md` — the seven checks, the numbers, the verdict, what it does not prove.
- `reports/LOG.md` — one row, four pipes, only for a card-level finding.
- Commit with explicit paths as `kapitaali <teppo@kapitaali.com>`. Never stage another lane's rows.

---

## 10. Hard stops

```
budgetTokens not 24000 / source not settings       VOID at turn 0
gateway older than the plugin file                 stop, ask for a restart
execute_code or terminal in the refs               VOID
all declares on turn 0                             VOID (one-turn session)
evictedTokens 0 on every turn                      NO-OP — report, do not reframe
both arms fail the same field                      fixture or checker defect, not an arm effect
coverage or replay non-zero                        VOID
cap would be crossed                               stop and ask
```

Never restart the gateway mid-cell. Never edit the fixture after seeing a result. Never re-title a
no-op as a paging result.

---

## 11. If the shape cannot be produced

The next artefact is a **multi-turn driver**, and it is the only path to a countable cell:

```
1  reads happen in the first 2-3 turns (material enters the session)
2  a middle of >= 6 turns where the model does other work (the selectable mass)
3  a final question whose answer requires the early material (so eviction has a cost)
4  determinism: same prompt sequence, same fixture digest, same toolset
5  the capture must show the turn spread — verify with len({declare.turn}) >= 10
```

Until that driver exists, no cell can count, and the honest action is to say so and stop — as with
every other unmeasurable condition in this card.

---

## 12. The one sentence

A cell counts only when the treatment was applied, the session had a middle, the surface was pinned,
the record re-derives, and the number came from the provider's own receipt. Anything less is a
measurement of the harness, and the harness has already been measured five times.
