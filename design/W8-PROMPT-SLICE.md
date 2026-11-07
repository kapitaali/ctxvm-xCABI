ROLE — W8 executor, the vertical slice after the 0.10.4 restart

You run two cells, then stop. Not a chunk, not the grid: the slice that proves the harness
can measure the thing the experiment is about. Everything else is repetition after this.

Read design/W8-RUNBOOK.md first — it is the protocol. This prompt adds only what changed
since chunk 1 and what this slice must prove. If this prompt and the repo disagree, the repo
wins; say so and stop.

STATE AT HANDOFF (verify, do not trust):
  cell 1 (t1 naive r1) is PILOT EVIDENCE, not a grid cell: it ran T1 at 33 parts, and T1 has
    since been re-scoped to 13 files / 13 parts / 50,257 declared tokens. Its $0.3303 stays
    spent and stays in the ledger.
  --plan must therefore print 48 of 48 cells pending. If it prints 47, the fixture-digest
    resume key is not working: stop and report, do not run.
  spend to date $0.8464 of $25.00. Plugin on disk 0.10.4; the gateway must now be one that
    started AFTER the sync.
  login/pricing: openai/gpt-6-luna on provider nous, paid row 0.10 / 0.50 / 0.01 cached.

WHAT CHANGED SINCE CHUNK 1 — check every line, stop on any miss:
  1. plugin 0.10.4 is installed and the gateway carrying it is running. A capture produced by
     a pre-0.10.4 gateway cannot prove its arm, and the slice exists to prove exactly that.
  2. The coverage sidecar now carries plugin.engine (null, or "ctxvm") and plugin.profile
     ("w8-naive" / "w8-paged"). tools/coverage_check.py accepts both.
  3. design/w8-run-plan.md 4d: NTR is defined on the PROVIDER RECEIPT, per cell —
     1 - (paged input)/(naive input), input = uncached + cached (+ cache-write when reported).
     Request-size evidence is the sidecar's perApiRequest series (peak and median).
  4. A `-z` capture may legitimately contain NO turn.render and NO call.meta. That is not a
     failure and must not be reported as one; record it as the known limitation in 4d.
  5. The resume key includes a fixture digest; a cell re-runs when its fixture changed.

YOUR JOB — two cells, in this order:
  cell A  t1 naive r1      -p w8-naive   context.engine compressor
  cell B  t1 paged r1      -p w8-paged   context.engine ctxvm, CTXVM_VBUDGET 24000

Per cell, all seven must hold before the cell counts:
  a) cmd.txt shows -p w8-<arm>, the pinned model and provider;
  b) usage.json: model openai/gpt-6-luna, provider nous; ledger row settled at the pinned row;
  c) capture triple present (.jsonl + .meta.json + .coverage.json);
  d) coverage manifest plugin.engine matches the arm — null for naive, "ctxvm" for paged —
     and plugin.profile matches the profile you passed. This is the check the slice exists
     for: a mismatch means the arm did not run, whatever the ledger says;
  e) tools/coverage_check.py exit 0, ctxvm replay exit 0, DQ scan still SHIP-UNBLOCKED;
  f) perApiRequest samples present (a cell with zero is an instrument failure);
  g) checker verdict recorded: PASS, or FAIL with the reason.

BEFORE THE FIRST PAID CALL, ask the owner:
  Q1  how many cells this sitting (default here: 2, the slice)
  Q2  one go for both, or a go before each
and record both answers at the top of the chunk report. Ask again before starting another
chunk after this one; do not decide that yourself.

INTERPRETING THE RESULT — say it plainly in the report:
  - naive solves, paged solves: the slice passed; report NTR from the receipts and the peak
    perApiRequest per arm. Then propose the next chunk, do not start it.
  - naive fails: name the failure class. lineShape-only mismatches are BYTE-COUNTING errors
    (6 of 13 files have bytes != chars; deltas 2 to 89) and must be reported separately from
    accuracy — never as an arm effect.
  - naive fails and paged fails for the SAME reason: that is a fixture defect, not an arm
    result (runbook hard stop). Report and stop; do not retry the same cell.
  - paged runs but plugin.engine is null: the profile did not reach the run. Stop.
  - paged's peak perApiRequest is not below naive's: the engine did not select. Report it as
    "no selection", do not present it as a paging result.

HARD STOPS:
  - --plan says 47 of 48, or any cell's engine/profile does not match its arm.
  - coverage_check or replay non-zero.
  - cap projection fires (spent + 2 x projected > 25).
  - the same cell aborts twice for the same infrastructure reason.
  A run is never interrupted mid-cell for convenience; if the machine must go down, let it
  finish or record ABORTED with the reason.

CLOSE:
  reports/RR-W8CHUNK-<date>-2.md (cells, minutes, tokens in/cached/out, cost, verdicts,
  the six checks per cell, arm evidence, what it does not prove), one row per cell in
  reports/W8-CHUNKLOG.md BEFORE you ask for the next go, one LOG row with four pipes, the
  ledger rows the runner wrote, an explicit staged commit, signed kapitaali. Never push.
  Then print: cells done / remaining / spend / the single next action.

START by printing --plan, the drift checks, and the two capture facts for cell 1 that this
slice will replace — then ask Q1 and Q2 and wait.
