# RR-W8B-REVIEW-20261110 — review of the W8B phases, and a corrected diagnosis

Reviewer: hermes lane (senior). Subject: `reports/RR-W8B-20261110.md` and the sessions it produced.
Every claim below was re-run against the store, the transcript and the gateway log.

## Verdicts

| item | verdict |
|---|---|
| Phase 0 capability | **PASS** — verified independently: `read_file`, correct byte count (16,602), 3 API calls, $0.00 |
| Phase 1 shape | **PASS with a caveat** — turns {0,1} only; the third prompt produced no read, so "3 prompts" gave 2 turns |
| Phase 2 naive | **PASS** — verified: 397 events, 84 declares, 22 turns, resident 87,578, 0 evictions, checker PASS (formatting note only) |
| Phase 2 paged | **NO DATA**, and the reported cause is **wrong** |
| Cost claim ($0) | **PASS** — every session row reads `estimated_cost_usd` 0.0, `billing_provider: nvidia` |

## The paged arm was not rate limited

The report says "NVIDIA NIM free-tier rate limiting". The evidence says otherwise:

```
gateway log            no 429, no throttle entry for the window
session transcript     turn 1: the model called `terminal`
                       -> tool: "Tool 'terminal' does not exist. Available tools: patch, read_file,
                          search_files, write_file"   at 13:59:37, three seconds after the prompt
                       then 7 assistant messages "Your request was not processed. Send it again if
                       you still want me to carry it out."
                       plus "[System: Your previous response was truncated]" notices
                       and at least one read_file result with file_size 0
prompt re-sends        the same prompt 1 sent ~30 times between 14:02 and 16:34, every ~3 minutes
```

"Your request was not processed…" is **model prose emitted after the unavailable-tool error**, not a
provider response. A rate limit would appear as an HTTP 429 in the gateway log and as a
`Retry-After`; neither exists.

So the paged arm never reached prompt 2 for a reason the report does not name: the model asked for a
tool that is not on the surface, then degenerated into empty/truncated turns, and something re-sent
prompt 1 every three minutes for two and a half hours.

## Why that matters more than the missing cell

1. **The surface pin is correct and the model does not respect it.** `terminal` is absent, as designed;
   the model asked for it anyway and did not recover. The naive arm, same surface, same prompt, did
   recover — so this is model variance, not a configuration error.
2. **The report's next action is a dead end.** "Wait for the rate limit to reset" would have waited for
   a limit that was never hit.
3. **The retry loop is unbounded and unlogged.** The driver sends each prompt once; the 30 re-sends
   came from outside it. Nothing stopped on the refusal marker, so a broken prompt cost 2.5 hours.
4. **No record exists.** The session never closed, so no capture flushed. Under the taxonomy this is
   not DATA-INVALID (which implies a bad record) — it is **NO RECORD**. That verdict is missing from
   `RR-W8ERRATA` §3 and should be added: a cell that leaves no capture cannot be classified at all.

## What the naive cell is worth

It is a valid control: 22 turns, 84 declares, 87,578 resident, 0 evictions, artefact parsed-equal. It
also shows the model solving the task with **61 `search_files` and 22 `read_file`** calls — a
search-heavy route that a paged arm would have to live with. It says nothing about eviction, because
the control has no engine.

## Fixes applied (this card)

```
tools/w8-driver.py   prompt 1 now names the three available tools and forbids others
                     a tool-not-exist marker or the "not processed" phrase aborts the cell
                     a subprocess timeout writes a stdout/stderr record instead of dying with a
                     traceback (that missing file is why the failure looked invisible)
```

The prompt change moves the prompt digest, so **the naive cell measured on prompt v1 cannot be pooled
with a v2 run**: both arms must be re-run after the change. That is free on this model (~5 min per
arm).

## Recommended next step

1. Re-run **both** arms on prompt v2, same code path, same sitting. Watch for `terminal` requests: if
   the model still asks for it, the run is not viable on this model and the plan should say so.
2. Keep a wall-clock cap per prompt (120 s is generous: the naive arm averages 4–7 s).
3. Add the NO RECORD verdict to the taxonomy and to the driver's verifier message.
