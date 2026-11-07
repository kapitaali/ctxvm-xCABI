# RR-W8RESCOPE-20261107 — T1 re-scoped by steps, the metric decided, and the 4–9 byte question answered

Card: the three items the chunk-1 session could not do from inside itself, minus the gateway
restart (an owner action). No paid call was made.

## 1. T1 re-scoped by steps, not by tokens

Cell 1 failed on `max_iterations_reached(150/150)` with 570 declares for 33 pages: the parts
were calls before any measurement happened. The lever is fewer, larger pages.

```
before   20 files, 33 parts, chunkBytes 12000, minRead 64,676 tokens
after    13 files, 13 parts, chunkBytes 60000, declared 50,257 tokens
         binaries 6, flags 21, lineShape 13 files, publicSurface 52 items
```

Thirteen reads instead of thirty-three, each file whole, so a read is also a measurement.
Verified:

```
materialize      t1: files=13 parts=13 bytes=201025
checker (expected)   PASS T1: flags.json equals the frozen vector          exit 0
checker (perturbed)  FAIL … lineShape.maxLineBytes: expected 100, got 104  exit 1
```

The declared floor still clears 45,000, which is what the pressure family requires; the call
count is now bounded by the file count rather than by the splitting rule.

## 2. The metric, decided — receipts, not turn rows

Cell 1 had no `turn.render` and no `call.meta` at all. The plugin's turn boundary is
`on_pre_llm_call`, which does not fire for a `-z` turn, so turn-level residency is not
derivable from the capture. Any metric defined on it would be empty for every cell.

Decision (written into `design/w8-run-plan.md` §4d):

- NTR per cell = `1 - (paged input) / (naive input)`, input = uncached + cached (plus
  cache-write when reported), read from the provider receipt.
- Request-size evidence comes from `perApiRequest` in the coverage sidecar: peak and median
  approx tokens per call, per arm; the "paged request smaller" gate is read there, with the
  quantile named.
- `turn.render` is used when present, never imputed; its absence is recorded as a limitation,
  and a cell with zero `perApiRequest` samples is an instrument failure that stops the chunk.

The sealed wire is untouched: one render per user turn stays its meaning, and the experiment
stops pretending to read a series the capture does not contain.

## 3. The 4–9 byte `maxLineBytes` question — answered

`task.md` has always said UTF-8 bytes, newline excluded, and `build_expected.py` recomputes
from file bytes. Measured over the 13 files:

```
files where bytes != chars: 6 of 13
deltas: 2 (tokens.rs, cli.rs, model.rs), 22 (render.rs), 71 (jsonl.rs), 89 (page_table.rs)
expected matches an independent byte count: True
```

So the earlier "off by 4–9 bytes on several files" is a **character-counting** error on lines
that carry multi-byte characters — a model measurement miss, not a checker or fixture gap.
The definition is not ambiguous, and the trap is deliberate: a fixture whose line shape can be
guessed from a match list is not a fixture.

One consequence for the analysis, not the fixture: a `lineShape`-only mismatch appearing in
**both** arms is a task-comprehension failure, not an arm difference, and must be reported
separately from accuracy. Failing to separate them would turn a counting mistake into a
paging result.

## 4. A re-scoped fixture invalidates the cells that measured the old one

Cell 1 ran T1 at 33 parts. The grid now runs 13. If the resume key stayed
`(round, task, arm)`, `--skip-done` would have skipped `t1 naive r1` and run
`t1 paged r1` on the new fixture — comparing a paged cell against a naive cell measured
on a different task. The key now includes a **fixture digest** (`task.md` + `fixture.json`
+ `profile.json` + `expected/*.json`, 12 hex), stamped into each cell's run directory:

```
pending: round 1 t1 naive
48 of 48 cells pending; 0 already in the ledger      (before: 47 of 48)
```

So cell 1 becomes pilot evidence: it stays in the ledger, it stays spent, and it no longer
counts as a grid cell. Its cost is not refunded and not retracted — only its status changes.

## What is still blocked, and by what

- The gateway restart onto plugin 0.10.4 is the owner's: it is the process the executing
  session runs in.
- Nothing else. The next paid cell is `t1 paged r1` on the re-scoped fixture, with
  `plugin.engine` present in its sidecar.
