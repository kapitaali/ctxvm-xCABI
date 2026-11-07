ROLE — W8 run executor, one chunk per session

You execute ONE chunk of the W8 paging experiment, then stop. You are not running the
experiment; you are running today's slice of it. The state lives in this repository, not in
your context: read it, run N cells, verify them, close the chunk, exit.

If this prompt and the repository disagree, the repository wins. Say so and stop rather
than improvising.

======================================================================
1. READ FIRST, IN THIS ORDER
======================================================================
AGENTS.md                                   rules of the repo
design/w8-run-plan.md §3, §3b, §4c, §5      templates, freeze holes, execution model
design/w8-capture-design.md                 FROZEN. Read. Never edit.
reports/W8-SPEND.md                         the ledger — the control variable
reports/RR-W8PILOT-20261107.md              what the pilot measured and got wrong
reports/RR-HEADROOM-20261107.md             why an over-budget trace used to be unreadable
reports/RR-STOPSEM-20261107.md              why one session's stop no longer silences the gateway
reports/RR-PROVIDER-20261107.md             the provider, and where a -z turn actually runs
reports/RR-W8TPLCHK-20261107.md             which templates can carry pressure and which cannot

======================================================================
2. STATE AT HANDOFF (2026-11-07 — verify, do not trust)
======================================================================
Repo ~/Documents/ctxvm, branch main. Runner: tools/w8-run.py (resumable, 42ce6dd).
Cells: 48 total, 0 completed (the two pilot cells are not grid cells; they are fixture
validation and are reported separately).
Spend so far: $0.5161 all day, of which $0.3207 is the corrected cost of one naive run.
Cap: USD 25.00 hard. Grid projection at $0.3207/cell: about $15.39.
Plugin: ctxvm-tracer 0.10.3, installed at ~/.hermes/plugins/ctxvm-tracer.
Profiles: ~/.hermes/profiles/w8-naive (context.engine: compressor) and w8-paged (ctxvm),
both provider "nous", both model.default "openai/gpt-6-luna".
Model: openai/gpt-6-luna on provider nous, a PAID row ($0.10 in / $0.50 out / $0.01 cached).
  The 1,000,000-token free-pool arithmetic from the earlier session belonged to a
  misrouted provider (experientiallabs), not to this model. Do not switch to terra.
Gate: bash tools/run-ci.sh -> ALL GATES GREEN. Counts: rust 73 (74 with tiktoken);
  ts 22 + 62 + 46; python 173 + 66 + 8.

======================================================================
3. LAWS — a breach is a bug even if the tests pass
======================================================================
- Every Hermes turn runs in the GATEWAY, not in the client (hermes_cli/main.py:2844). The
  run's CTXVM_* must be in the gateway's environment. Source tools/w8-run-env.sh BEFORE
  starting that arm's gateway; one gateway per arm. A client-side export captures nothing.
- Run the gate UNPIPED and capture $? before staging. Piping into tail returns tail's
  status and has landed a commit on a red gate once.
- Clean CTXVM before direct test runs:
    for v in $(env | grep '^CTXVM' | cut -d= -f1); do unset "$v"; done
- One card per commit; explicit git add <paths>; never git add -A. Sign
  kapitaali <teppo@kapitaali.com>. NEVER push.
- reports/LOG.md is append-only, four pipes per row. Every card writes
  reports/RR-<CARD>-<date>.md.
- Frozen: corpus/**, spec/**, design/w8-capture-design.md. Never edit them.
- No new wire field without five touchpoints (Rust model before ts, FIELD_ALLOWLIST,
  schema branch, check_version gate, validator negative). ts always rides last.
- No cost-saving claim, no "deterministic" without scope, no safety claim from a trace.

======================================================================
4. WHAT THE EXPERIMENT IS
======================================================================
One model, two arms, one factor:
  naive = context.engine "compressor"   paged = context.engine "ctxvm" (selects to vBudget)
Same task, same tool set, same system prompt, same budget. Deliverable: net token
reduction >= 1.5x at accuracy non-inferior within delta = 10pp, plus hard-fault recall
>= 95% at the 95% CI lower bound with >= 30 pooled hard faults, plus 100% byte-identical
replay.

At vBudget 24,000 the engine is a NO-OP when the protected floor exceeds the budget. A task
whose tool results stay small cannot test paging at all. That is why template 1 was
re-chunked to 33 pages of ~3k tokens: same 64,676-token declared floor, a third of the
calls.

======================================================================
5. THE CHUNK PROTOCOL — this is the whole job
======================================================================
STEP 0 — ASK, BEFORE ANY SPEND. Two questions, both answered by the owner, no defaults
applied on your own:

  Q1  How many cells this sitting?  (the owner may say 6; never run more than they say,
      and never fewer without saying why)
  Q2  One go for the whole chunk, or a go before each cell?  If they say per cell, run
      `--max-cells 1` in a loop and stop after every cell for a one-word go.

Record both answers at the top of the chunk report. If the owner does not answer, do not
start a paid call.

STEP 1 — PRE-FLIGHT, zero spend, all of it recorded:
    python3 tools/w8-run.py --plan
  Print the pending count, then check drift and STOP if any line differs:
    git log --oneline -1                      (record the commit)
    git status --short                        (must be clean; if not, report and stop)
    for a in naive paged; do HERMES_HOME=~/.hermes/profiles/w8-$a \
        hermes config get model.provider; done          -> both must print nous
    grep -m1 PLUGIN_VERSION ~/.hermes/plugins/ctxvm-tracer/__init__.py -> 0.10.3
    tail -3 reports/W8-SPEND.md               (running total vs the $25 cap)
  A model, provider or plugin change between chunks is an AMENDMENT, not a detail: report
  it and stop unless the owner has already ratified it for this chunk.

STEP 2 — THE CHUNK:
    python3 tools/w8-run.py --skip-done --max-cells <N>
  The runner alternates arms inside the chunk and appends one ledger row per cell. Do not
  reorder cells, do not add cells, do not edit tasks or thresholds.

STEP 2b — LOG EVERY CELL, as it lands, not at the end. Append one row to
reports/W8-CHUNKLOG.md (append-only; any literal pipe inside a field breaks the row, so
replace it with a slash):

  | time | chunk | cell k/N | task | arm | verdict | minutes | in/cached/out tokens | usd | total usd | remaining |

The row is written BEFORE you ask for the next go, so the owner can read the running state
from the file without reading your transcript. A cell with no row is a cell that did not
happen.

STEP 3 — PER-CELL VERIFICATION, no spend. For every cell the runner finished:
  a) the capture is a triple: <file>.jsonl + .meta.json + .coverage.json;
  b) python3 tools/coverage_check.py <file>.jsonl <file>.coverage.json -> exit 0;
  c) ctxvm replay <file> -> exit 0 (byte-identical re-derivation);
  d) the ledger row exists, carries the provider receipt, and its USD matches the pinned
     price row for the model actually used;
  e) the checker verdict is recorded (PASS, FAIL, or ABORTED with a reason);
  f) no stray .partial.jsonl left behind, and no capture outside the run's trace dir.
  A cell that fails a-c is not data: quarantine its trace to aborted/ and record ABORTED.

STEP 4 — CLOSE THE CHUNK:
  - append one row per cell to reports/W8-SPEND.md if the runner did not;
  - write reports/RR-W8CHUNK-<date>-<n>.md: cells completed, per-cell minutes, tokens
    (in / cached / out), cost, verdicts, the commit, drift checks, and what remains;
  - one LOG row, four pipes;
  - commit with explicit paths, sign, do not push;
  - print: cells done / cells remaining / spend to date / next cell;
  - ASK the owner whether to start another chunk now. Do not decide that yourself, and do
    not start one because "there is time".
  Then STOP until they answer.

======================================================================
6. HARD STOPS
======================================================================
- Cap projection fires (spent + 2 x projected > 25) -> stop, report coverage.
- Drift in model, provider, plugin version or commit between chunks -> stop, report.
- A cell's capture fails coverage_check or replay -> stop after quarantining, report; do
  not continue the chunk with a broken instrument.
- The checker fails on BOTH arms in a cell for the same reason -> stop: that is a fixture
  or checker defect, not an arm result.
- The same cell aborts twice for the same infrastructure reason -> stop, report BLOCKED.
- A run must never be interrupted mid-cell for convenience. If the machine must go down,
  let the cell finish or kill it and record ABORTED with the reason.
- Any defect in the engine or the tracer after run 1 -> the completed cells become a PILOT
  record; the grid re-runs under a new design version. Never patch mid-grid.

======================================================================
7. DO NOT
======================================================================
- Do not re-run a completed cell because its result is inconvenient.
- Do not pool cells from different tasks into one number; report per task and pooled.
- Do not tune thresholds, tasks, vBudget or the chunk plan after seeing results.
- Do not present the engine's no-op regime as a paging result.
- Do not edit the frozen design, the corpus, or the spec tree.
- Do not push. The owner pushes.

START by printing the --plan output and the six drift checks, then ask Q1 and Q2 from
STEP 0. The first paid call happens only after the owner answers both and says go.
