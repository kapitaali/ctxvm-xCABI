ROLE — W8 executor: run ONE diagnostic cell. Then stop.

This cell answers a question four earlier cells could not: **does the ctxvm engine act at a
24,000-token budget on this harness, or does the protected floor sit above the budget and make
selection impossible?** Every previous attempt was void for a reason now fixed or known: a naive arm
with `execute_code` (no `-t`), a paged arm at the 200,000 default, and an arm counter that cannot
distinguish profiles.

Do not build a fourth witness. Do not scale to a grid. Run the cell, verify it, report five lines.

======================================================================
1. READ FIRST
======================================================================
AGENTS.md                                   laws
handoff/LANES.md                            your lane's paths; shared-file rules
design/w8-run-plan.md §4d, §4e              metric + decisions in force
design/w8-cache-stable-selection.md         the arithmetic this cell feeds
design/w8-tasks/T-A.md                      task, artefact, fixture
reports/RR-BUDGET-20261109.md               why the last pair was a no-op

======================================================================
2. STATE (verify, do not trust)
======================================================================
- 0 cells count. 48 pending. Spend $1.3562 of $25.00 (remaining $23.64).
- Plugin **0.10.11** is required. It reads the budget from
  `plugins.entries.ctxvm-tracer.settings.budgetTokens` in the **serving profile's** config:
  `w8-paged` declares 24000, `w8-naive` declares nothing. Precedence: setting > env > 200000.
- The last pair ran at 200,000 in BOTH arms (`resident + headroom = 200,000`, `evictedTokens: 0`)
  because nothing declared the budget. That pair is a no-op, not a paging result.
- `-t file` resolves to `patch, read_file, search_files, write_file` — no `execute_code`, no
  `terminal`. A cell that omits `-t` is void: the model answers with one code call and never holds
  the material.
- Task A: 14 files × 250 lines, floor ≈ 54,700 declared tokens; a pinned naive cell completed in
  8 calls for $0.0221 with every value correct (32 read, 4 search, 1 write, peak 59,793).

Verify before spending (free, ~10 s):

  pgrep -af "hermes.*gateway" | awk '{print $1}' | head -1 | xargs -I{} ps -o pid=,lstart= -p {}
  grep -m1 PLUGIN_VERSION ~/.hermes/plugins/ctxvm-tracer/__init__.py
  hermes config get plugins.entries.ctxvm-tracer.settings.budgetTokens -p w8-paged   # expect 24000
  hermes config get plugins.entries.ctxvm-tracer.settings.budgetTokens -p w8-naive   # expect "not set"

If the serving process started BEFORE the plugin file's mtime, the gateway runs older code and the
budget cannot reach the engine. Stop and ask for a restart; do not run the cell.

======================================================================
3. THE CELL
======================================================================
One treatment cell on T-A, against the existing naive reference. Do not re-buy the control arm unless
that reference is missing.

  mkdir -p ~/.local/state/ctxvm/w8-runs/t-a-paged-24k
  hermes -p w8-paged -z "<the T-A task text>" \
      -m openai/gpt-6-luna --provider nous \
      -t file \
      --in <workspace: the 14 fixture files, no artefact yet> \
      --usage-file ~/.local/state/ctxvm/w8-runs/t-a-paged-24k/usage.json

Do NOT export `CTXVM_*` in the shell. The budget is a profile setting now, and an env var would mask
whether the setting works — which is half of what this cell tests.

======================================================================
4. ATTRIBUTION — what you assert, and what you cannot
======================================================================
This host cannot attest an arm inside a capture. Three witnesses were built and all three were
falsified (construction read as activation; a module counter shared through the flat sibling import;
an instance counter lost to the per-agent deepcopy, then shared through the shared plugin directory).
The plugin lives in `~/.hermes/plugins/`, which is one module for every profile: one `state`, one
engine object, one counter. Both arms of the last pair read `engineSelections: 14`.

So the arm is attested by **you**, in the ledger row: the `-p` you passed, the model, the provider,
the timestamp, the cost. The capture corroborates:
`engineSelections > 0` means *an* engine ran in the process — never that this arm used it.

======================================================================
5. ACCEPTANCE — seven checks, from the capture
======================================================================
```
1  sidecar plugin.budgetTokens == 24000 and budgetSource == "settings"
      -> otherwise the cell is VOID at turn 0. Stop and report the values, not a result.
2  sidecar plugin.engineSelections > 0               (the hook was called at all)
3  turn.render evictedTokens > 0 on at least one turn
      -> zero on every turn means the engine is a NO-OP at this budget. That is the finding this
         cell exists to produce; report it plainly.
4  peak prefix from perApiRequest.approxInputTokens, against the naive peak 59,793
5  refs by tool: read_file / search_files / write_file only; no execute_code, no terminal
6  coverage: python3 tools/coverage_check.py <file>.jsonl <file>.coverage.json  -> 0
   replay:   ./rust/target/release/replay <file>  -> 0, byte-identical
7  checker:  python3 <checker> <fixture-dir> <artefact-path>  -> 0 PASS / 1 FAIL
```

The checker **must take its paths as arguments and print what it read**. The first T-A checker
hardcoded both paths and validated a reference copy instead of the model's artefact; a PASS from a
checker that ignores its arguments is not evidence.

The checker's gate is the **PARSED** artefact — same keys, same values, same ordering — with
canonical formatting recorded separately. Byte-exactness is JSON style, not accuracy: both arms of
the last pair wrote per-file objects inline and both would have "failed" on indentation.

======================================================================
6. INTERPRET, DO NOT SPIN
======================================================================
- Report the cache columns (`cache_read`, `cache_write`) and dollars beside any token ratio. On this
  harness the cache is the dominant term: the last pair spent $0.0982 of $0.1264 on input alone.
- Paged artefact parsed-equal and `evictedTokens > 0`: a real measurement. Give the ratio, the peak,
  the two costs, and what it does not prove.
- `evictedTokens == 0` everywhere: NO-OP. Do not describe it as a paging result; it says the floor
  exceeds the budget on this harness, which is a fact about the floor.
- Both arms fail on the same field: fixture or checker defect. Stop.
- `engineSelections == 0`: the hook never ran — check the gateway version and the profile, then stop.

Accuracy is the gate. Tokens are the finding. Never report one without the other.

======================================================================
7. CLOSE
======================================================================
- Append the cell to `reports/RR-W8CELL-20261109.md` (or a new `RR-W8CELL-<date>.md`): the seven
  checks, the numbers, the verdict, the cost, what it does not prove.
- One row in `reports/W8-CHUNKLOG.md` **before** asking for the next cell; ledger in `W8-SPEND.md`.
- The cell counts only if checks 1–3 pass; otherwise record VOID or NO-OP with the reason.
- One LOG row, four pipes; explicit staged paths; commit as `kapitaali <teppo@kapitaali.com>`.
- Then print: cells done / remaining / spend / the single next action, and **ask** before another.

Results live in `experiments/` (gitignored until there is enough data to publish); the numbers live in
`reports/RR-*.md` and `~/.local/state/ctxvm/w8-runs/`. Evidence does not go in `/tmp`.

======================================================================
8. HARD STOPS
======================================================================
- `budgetTokens` not 24000, or `budgetSource` not `settings` → VOID at turn 0.
- The gateway predates the plugin file → stop and ask for a restart.
- `execute_code` or `terminal` in the refs → void; the surface was not pinned.
- Any cell fails coverage or replay.
- Both arms fail on the same field.
- Spend would exceed the remaining $23.64.
- A checker that cannot take its paths as arguments.
- Never restart the gateway mid-cell.

======================================================================
9. DO NOT
======================================================================
- Do not build a fourth arm witness.
- Do not re-buy the control arm; the naive reference exists.
- Do not restore `max_line`/`min_line`.
- Do not run more than one treatment cell in this sitting.
- Do not present a no-op, a search-bound run, or an inline-formatting mismatch as a paging result.
- Do not touch `research/**`, `packages/**`, `spec/**`, `corpus/**`.

Five lines at the end: budget + source, selections, evictions, peak prefix vs naive, cost. No prose.
