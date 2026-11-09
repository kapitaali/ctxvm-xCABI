ROLE — W8 executor: run the next cell, or the pair. Then stop.

You are running cells of a context-policy experiment, not building an instrument. Every instrument
question that could be answered by reading code has been answered by measurement; three probes and
three plugin versions were spent learning that this host cannot attest an arm inside a capture. Do
not add a fourth witness. Run the cell, verify it, report.

======================================================================
1. READ FIRST
======================================================================
AGENTS.md                                   laws
handoff/LANES.md                            your lane's paths; shared-file rules
design/w8-run-plan.md §3b, §4e              the decisions in force (D-A … D-J)
design/w8-tasks/T-A.md                      the task, the artefact, the fixture
design/w8-tasks/REVIEW.md                   what was wrong with the first draft and why
reports/RR-W8TACHECK-20261109.md            the instrument findings, including two falsified witnesses

======================================================================
2. STATE (verify, do not trust)
======================================================================
- 0 cells count. 48 pending. Spend ≈ $1.1587 of the $25 cap.
- Task A is the only viable task: 14 files × 250 lines, floor ≈ 54,700 tokens, a naive cell finished
  in 16 calls for $0.0359 with `long`/`short`/`lines`/`bytes` all correct.
- `max_line`/`min_line` are **removed** from the artefact. They were wrong in all 14 files across
  three runs; a gate the model cannot meet measures arithmetic, not paging.
- Plugin 0.10.9 on disk, gateway on 0.10.8 (started 13:41:59). The version difference is understood
  and does not block: attribution is runner-side, see §4.
- One gateway, all profiles, no restart needed for anything in this prompt.

======================================================================
3. THE CELL(S)
======================================================================
Run the pair on T-A, or the paged arm alone if the owner limits the sitting:

  naive   -p w8-naive   context.engine compressor
  paged   -p w8-paged   context.engine ctxvm, vBudget 24,000 (the plugin default)

Exact call shape — adapt paths, keep the flags:

  mkdir -p /tmp/w8cell
  hermes -p w8-paged -z "<the T-A task text>" \
      -m openai/gpt-6-luna --provider nous \
      --in <workspace with the fixture and an empty artefact slot> \
      --usage-file /tmp/w8cell/paged-usage.json

Do NOT export `CTXVM_*` in the shell: the gateway's environment decides capture, and a client export
changes nothing but the record.

======================================================================
4. ATTRIBUTION — what you assert, and what you cannot
======================================================================
This host cannot attest an arm inside a capture. Two witnesses were built and both were falsified:

```
module counter   shared across profiles through the flat sibling import
                 (-p w8-naive read 1 right after a paged session)
ctx.get_config   reads plugins.entries.<id>.settings.*, not the profile's context.engine
                 (returned null for a profile whose config says ctxvm)
```

So the arm is attested by **you**, in the ledger row: the `-p` you passed, the model, the provider,
the timestamp, the cost. The capture **corroborates** it:

```
paged   engineSelections > 0    a 14-read task does reach select_context
naive   engineSelections == 0   the compressor profile never calls it
```

If the paged cell shows `engineSelections: 0`, the engine did not engage: the run is a **pilot
record**, not a cell. Say so and stop; do not reclassify it.

======================================================================
5. VERIFY EACH CELL — all seven, or the cell does not count
======================================================================
```
1  usage.json      api_calls, cost, model openai/gpt-6-luna, provider nous
2  ledger row      arm, model, provider, timestamp, cost, verdict — written by you
3  capture triple  <file>.jsonl + .meta.json + .coverage.json in the gateway's trace dir
4  coverage        python3 tools/coverage_check.py <file>.jsonl <file>.coverage.json  -> 0
5  replay          ./rust/target/release/replay <file>  -> 0 (byte-identical re-derivation)
6  engine          sidecar plugin.engineSelections matches the arm (see §4)
7  checker         python3 <checker> <fixture-dir> <artefact-path>  -> 0 PASS / 1 FAIL
```

The checker **must take its paths as arguments and print what it read**. The first T-A checker
hardcoded both paths and validated a reference copy instead of the model's artefact; a PASS from a
checker that ignores its arguments is not evidence. If the checker you have cannot do this, fix it
before the cell, not after.

======================================================================
6. INTERPRET, DO NOT SPIN
======================================================================
- Both arms PASS: report the pair. Token ratio from the **provider receipt**
  (`1 - paged_input / naive_input`, input = uncached + cached), peak per-request from the sidecar's
  `perApiRequest` series, and the two costs. That is the first real number this card has produced.
- Naive PASS, paged FAIL: the paging arm lost accuracy. Report the failing fields verbatim; do not
  describe it as "a paging result" until the failure is checked against the fixture.
- Both FAIL on the same field: fixture or checker defect, not an arm result. Stop.
- Paged shows `engineSelections: 0`: no engine. Pilot record. Stop.
- `search_files` truncation is a possible wrong-answer cause; before blaming the model, check whether
  the answer used partial data (`limit` in the search call, `messageCount` in the sidecar).

Accuracy is the gate. Tokens are the finding. Never report one without the other.

======================================================================
7. CLOSE
======================================================================
- `reports/RR-W8CELL-<date>.md`: the cells, their seven checks, the receipts, the ratio, what it does
  not prove, and the commit.
- One row per cell in `reports/W8-CHUNKLOG.md` **before** you ask for the next one.
- Ledger rows settled in `reports/W8-SPEND.md`.
- One LOG row, four pipes; explicit staged paths; commit as `kapitaali <teppo@kapitaali.com>`.
- Then print: cells done / remaining / spend / the single next action, and **ask** before starting
  another cell.

Results live in `experiments/` (gitignored until there is enough data to publish); the numbers live
in `reports/RR-*.md`. Evidence does not go in `/tmp`.

======================================================================
8. HARD STOPS
======================================================================
- The paged cell shows `engineSelections: 0`.
- Any cell fails coverage or replay.
- Both arms fail on the same field.
- The cap projection fires (`spent + 2 × projected > 25`).
- A checker that cannot take its paths as arguments.

======================================================================
9. DO NOT
======================================================================
- Do not build a fourth arm witness. Two were falsified; the answer is runner-side attribution.
- Do not restore `max_line`/`min_line`.
- Do not restart the gateway for this prompt.
- Do not present the engine's no-op regime, or a search-bound run, as a paging result.
- Do not touch `research/**`, `packages/**`, `spec/**`, `corpus/**`.
